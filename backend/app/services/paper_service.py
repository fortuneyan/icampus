"""
Smart Paper Generation System - Service Layer

Contains:
1. GreedyPaperGenerator - Greedy generation algorithm
2. DiagnosticPaperGenerator - Diagnostic generation
3. ABPaperGenerator - A/B paper generation
4. PaperService - Paper service
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import random

from app.models.paper import SmartPaper as Paper, SmartPaperQuestion as PaperQuestion
from app.models.question import Question
from app.schemas.paper import (
    PaperConstraints,
    PaperCreate,
    PaperUpdate,
    PaperGenerateRequest,
    DiagnosticGenerateRequest,
    PaperGenerationResult,
    PaperGenerationError,
    ABPaperRequest,
)


class GreedyPaperGenerator:
    """
    Greedy paper generation algorithm
    
    Core idea:
    1. Sort by knowledge point priority
    2. For each point, select questions closest to target difficulty
    3. Check if overall distribution meets constraints
    4. Adjust if needed
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate(self, constraints: PaperConstraints) -> PaperGenerationResult:
        """Generate paper"""
        constraints.validate_conflicts()
        
        candidates = await self._query_questions(constraints)
        
        if len(candidates) < constraints.total_count:
            raise PaperGenerationError(
                f"Insufficient questions: need {constraints.total_count}, available {len(candidates)}"
            )
        
        selected = self._greedy_select(candidates, constraints)
        
        difficulty_dist = self._calculate_distribution(selected, key="difficulty", levels=[1, 2, 3, 4, 5])
        cognitive_dist = self._calculate_distribution(
            selected, key="cognitive_level", levels=["L1", "L2", "L3", "L4", "L5", "L6"]
        )
        knowledge_coverage = self._calculate_knowledge_coverage(
            selected, constraints.target_knowledge_points
        )
        
        warnings = self._generate_warnings(constraints, difficulty_dist, knowledge_coverage)
        
        return PaperGenerationResult(
            paper=None,
            questions=selected,
            difficulty_distribution=difficulty_dist,
            knowledge_coverage=knowledge_coverage,
            cognitive_distribution=cognitive_dist,
            warnings=warnings,
        )
    
    async def _query_questions(self, constraints: PaperConstraints) -> List[Dict[str, Any]]:
        """Query available questions"""
        query = select(Question).where(
            Question.is_deleted == False,
            Question.review_status == "approved" if constraints.require_reviewed else True,
            Question.has_answer == True,
        )
        
        if constraints.target_knowledge_points:
            for kp in constraints.target_knowledge_points:
                query = query.where(Question.knowledge_points.contains([kp]))
        
        if constraints.exclude_knowledge_points:
            for kp in constraints.exclude_knowledge_points:
                query = query.where(~Question.knowledge_points.contains([kp]))
        
        if constraints.difficulty_distribution:
            difficulties = [int(d) for d in constraints.difficulty_distribution.keys()]
            query = query.where(Question.difficulty.in_(difficulties))
        
        if constraints.question_type_counts:
            types = list(constraints.question_type_counts.keys())
            query = query.where(Question.question_type.in_(types))
        
        if constraints.min_usage_count > 0:
            query = query.where(Question.usage_count >= constraints.min_usage_count)
        
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        return [
            {
                "id": str(q.id),
                "content": q.content,
                "question_type": q.question_type,
                "options": q.options,
                "answer": q.answer,
                "analysis": q.analysis,
                "difficulty": q.difficulty,
                "cognitive_level": q.cognitive_level,
                "knowledge_points": q.knowledge_points or [],
                "score": float(q.score),
            }
            for q in questions
        ]
    
    def _greedy_select(
        self, 
        candidates: List[Dict[str, Any]], 
        constraints: PaperConstraints
    ) -> List[Dict[str, Any]]:
        """Greedy selection"""
        selected = []
        remaining = list(candidates)
        
        if constraints.target_knowledge_points:
            selected, remaining = self._select_by_knowledge_points(remaining, constraints)
        
        if constraints.question_type_counts:
            selected, remaining = self._select_by_type(
                selected, remaining, constraints.question_type_counts
            )
        
        while len(selected) < constraints.total_count and remaining:
            best = self._select_best_candidate(remaining, constraints)
            if best:
                selected.append(best)
                remaining.remove(best)
            else:
                break
        
        return selected[:constraints.total_count]
    
    def _select_by_knowledge_points(
        self,
        candidates: List[Dict[str, Any]],
        constraints: PaperConstraints
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Select by knowledge points"""
        selected = []
        remaining = list(candidates)
        
        for kp in constraints.target_knowledge_points:
            if len(selected) >= constraints.total_count:
                break
            
            kp_candidates = [
                q for q in remaining
                if q.get("knowledge_points") and kp in q["knowledge_points"]
            ]
            
            if kp_candidates:
                best = self._select_best_by_difficulty(kp_candidates, constraints.target_difficulty)
                if best:
                    selected.append(best)
                    remaining.remove(best)
        
        return selected, remaining
    
    def _select_by_type(
        self,
        selected: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        type_counts: Dict[str, int]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Select by question type"""
        remaining = list(candidates)
        selected_types = Counter(q["question_type"] for q in selected)
        
        for qtype, target_count in type_counts.items():
            current_count = selected_types.get(qtype, 0)
            needed = target_count - current_count
            
            if needed > 0:
                type_candidates = [q for q in remaining if q["question_type"] == qtype]
                
                for _ in range(needed):
                    if not type_candidates:
                        break
                    best = type_candidates.pop(0)
                    selected.append(best)
                    remaining.remove(best)
        
        return selected, remaining
    
    def _select_best_candidate(
        self,
        candidates: List[Dict[str, Any]],
        constraints: PaperConstraints
    ) -> Optional[Dict[str, Any]]:
        """Select best candidate"""
        if not candidates:
            return None
        
        if constraints.difficulty_distribution:
            target_difficulty = self._get_target_difficulty(constraints)
            return self._select_best_by_difficulty(candidates, target_difficulty)
        
        return random.choice(candidates)
    
    def _select_best_by_difficulty(
        self,
        candidates: List[Dict[str, Any]],
        target_difficulty: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Select closest difficulty"""
        if not candidates:
            return None
        
        if target_difficulty is None:
            return candidates[0]
        
        return min(
            candidates,
            key=lambda q: abs(q.get("difficulty", 3) - target_difficulty)
        )
    
    def _select_best_by_score(
        self,
        candidates: List[Dict[str, Any]],
        target_score: float
    ) -> Optional[Dict[str, Any]]:
        """Select closest score"""
        if not candidates:
            return None
        
        return min(
            candidates,
            key=lambda q: abs(q.get("score", 5) - target_score)
        )
    
    def _get_target_difficulty(self, constraints: PaperConstraints) -> float:
        """Calculate target difficulty from distribution"""
        if not constraints.difficulty_distribution:
            return 3.0
        
        dist = constraints.difficulty_distribution
        return sum(int(d) * p for d, p in dist.items())
    
    def _calculate_distribution(
        self,
        questions: List[Dict[str, Any]],
        key: str = "difficulty",
        levels: List[Any] = None
    ) -> Dict[str, float]:
        """Calculate distribution (defaults to difficulty distribution with int keys)"""
        if levels is None:
            levels = [1, 2, 3, 4, 5] if key == "difficulty" else ["L1", "L2", "L3", "L4", "L5", "L6"]
        
        if not questions:
            return {l: 0.0 for l in levels}
        
        counter = Counter(q.get(key, levels[0]) for q in questions)
        total = len(questions)
        
        return {
            level: round(counter.get(level, 0) / total, 3)
            for level in levels
        }
    
    def _calculate_knowledge_coverage(
        self,
        questions: List[Dict[str, Any]],
        target_kps: List[str]
    ) -> Dict[str, float]:
        """Calculate knowledge coverage"""
        if not target_kps:
            return {"总体覆盖率": 1.0}
        
        covered = Counter()
        for q in questions:
            for kp in q.get("knowledge_points", []):
                covered[kp] += 1
        
        coverage = {kp: 1.0 if covered.get(kp, 0) > 0 else 0.0 for kp in target_kps}
        coverage["总体覆盖率"] = round(
            sum(1 for v in coverage.values() if v > 0) / len(target_kps), 3
        )
        
        return coverage
    
    def _generate_warnings(
        self,
        constraints: PaperConstraints,
        difficulty_dist: Dict[str, float],
        knowledge_coverage: Dict[str, float]
    ) -> List[str]:
        """Generate warnings"""
        warnings = []
        
        if constraints.difficulty_distribution:
            for level, target in constraints.difficulty_distribution.items():
                actual = difficulty_dist.get(level, 0.0)
                if abs(actual - target) > 0.1:
                    warnings.append(
                        f"Difficulty {level} actual ({actual:.1%}) differs from target ({target:.1%})"
                    )
        
        overall = knowledge_coverage.get("总体覆盖率", 1.0)
        if overall < 1.0:
            warnings.append(f"Knowledge coverage only {overall:.1%}, some points not covered")
        
        return warnings


class DiagnosticPaperGenerator(GreedyPaperGenerator):
    """Diagnostic paper generation based on student diagnosis"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db)
    
    async def generate_from_diagnosis(
        self,
        request: DiagnosticGenerateRequest,
        constraints: PaperConstraints
    ) -> PaperGenerationResult:
        """Generate paper from diagnosis report"""
        adjusted_constraints = self._adjust_constraints(request, constraints)
        return await super().generate(adjusted_constraints)
    
    def _adjust_constraints(
        self,
        request: DiagnosticGenerateRequest,
        base_constraints: PaperConstraints
    ) -> PaperConstraints:
        """Adjust constraints for diagnosis"""
        weak_points = request.weak_points
        target_kps = list(set(weak_points + base_constraints.target_knowledge_points))
        
        difficulty_dist = base_constraints.difficulty_distribution or {
            "1": 0.1, "2": 0.4, "3": 0.4, "4": 0.1
        }
        
        adjusted_dist = self._adjust_difficulty_for_mastery(
            base_dist=difficulty_dist,
            mastery_level=self._calculate_avg_mastery(request.mastery_levels)
        )
        
        return PaperConstraints(
            total_count=base_constraints.total_count,
            total_score=base_constraints.total_score,
            target_knowledge_points=target_kps,
            difficulty_distribution=adjusted_dist,
            question_type_counts=base_constraints.question_type_counts,
        )
    
    def _adjust_difficulty_for_mastery(
        self,
        base_dist: Dict[str, float],
        mastery_level: float
    ) -> Dict[str, float]:
        """Adjust difficulty for mastery level (returns int keys)"""
        if mastery_level >= 0.7:
            # Convert string keys to int if needed
            return {int(k): v for k, v in base_dist.items()} if isinstance(list(base_dist.keys())[0], str) else base_dist
        
        if mastery_level < 0.4:
            return {1: 0.2, 2: 0.4, 3: 0.3, 4: 0.1, 5: 0.0}
        elif mastery_level < 0.6:
            return {1: 0.15, 2: 0.35, 3: 0.35, 4: 0.15, 5: 0.0}
        return {int(k): v for k, v in base_dist.items()} if isinstance(list(base_dist.keys())[0], str) else base_dist
    
    def _calculate_avg_mastery(self, mastery_levels: Dict[str, float]) -> float:
        """Calculate average mastery"""
        if not mastery_levels:
            return 0.5
        return sum(mastery_levels.values()) / len(mastery_levels)
    
    def _extract_weak_points(
        self,
        diagnosis: Dict[str, Any],
        threshold: float = 0.4
    ) -> List[str]:
        """Extract weak points from diagnosis"""
        mastery_levels = diagnosis.get("mastery_levels", {})
        return [kp for kp, level in mastery_levels.items() if level < threshold]
    
    def _build_diagnostic_constraints(
        self,
        diagnosis: Dict[str, Any],
        total_count: int = 20,
        total_score: float = 100.0,
        base_constraints: Dict[str, Any] = None
    ) -> PaperConstraints:
        """Build constraints from diagnosis report"""
        weak_kps = self._extract_weak_points(diagnosis)
        mastery_levels = diagnosis.get("mastery_levels", {})
        avg_mastery = self._calculate_avg_mastery(mastery_levels)
        
        # Use provided values or defaults
        count = base_constraints.get("total_count", total_count) if base_constraints else total_count
        score = base_constraints.get("total_score", total_score) if base_constraints else total_score
        
        # Adjust difficulty based on mastery level
        adjusted_dist = self._adjust_difficulty_for_mastery(
            base_dist={1: 0.1, 2: 0.4, 3: 0.4, 4: 0.1},
            mastery_level=avg_mastery
        )
        
        return PaperConstraints(
            total_count=count,
            total_score=score,
            target_knowledge_points=weak_kps,
            difficulty_distribution={str(k): v for k, v in adjusted_dist.items()},
            require_reviewed=True,
        )


class ABPaperGenerator:
    """A/B paper generator"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_paired_paper(
        self,
        paper_a: Paper,
        request: ABPaperRequest
    ) -> Tuple[Paper, float]:
        """Generate paired B paper"""
        a_questions = await self._get_paper_questions(paper_a)
        b_questions = []
        
        for q in a_questions:
            similar = await self._find_similar_question(q)
            if similar:
                b_questions.append(similar)
            else:
                b_questions.append(q)
        
        paper_b = Paper(
            title=request.title_b or f"{paper_a.title} (B)",
            subject=paper_a.subject,
            grade_level=paper_a.grade_level,
            paper_type=paper_a.paper_type,
            generation_mode="ab_paired",
            constraints=paper_a.constraints,
            question_ids=[q["id"] for q in b_questions],
            question_count=len(b_questions),
            total_score=paper_a.total_score,
            estimated_time=paper_a.estimated_time,
            difficulty_distribution=paper_a.difficulty_distribution,
            is_paired=True,
            is_paper_a=False,
            paired_paper_id=paper_a.id,
            status="draft",
        )
        
        self.db.add(paper_b)
        await self.db.flush()
        
        for i, q in enumerate(b_questions):
            pq = PaperQuestion(
                paper_id=paper_b.id,
                question_id=UUID(q["id"]),
                order=i + 1,
                score=float(q.get("score", 5)),
                appears_in="B",
            )
            self.db.add(pq)
        
        paper_a.is_paired = True
        paper_a.paired_paper_id = paper_b.id
        
        await self.db.commit()
        similarity = self._calculate_paper_similarity(a_questions, b_questions)
        
        return paper_b, similarity
    
    async def _get_paper_questions(self, paper: Paper) -> List[Dict[str, Any]]:
        """Get paper questions"""
        if not paper.question_ids:
            return []
        
        query = select(Question).where(Question.id.in_(paper.question_ids))
        result = await self.db.execute(query)
        questions = result.scalars().all()
        
        id_order = {str(qid): i for i, qid in enumerate(paper.question_ids)}
        
        return sorted(
            [
                {
                    "id": str(q.id),
                    "content": q.content,
                    "question_type": q.question_type,
                    "difficulty": q.difficulty,
                    "knowledge_points": q.knowledge_points or [],
                }
                for q in questions
            ],
            key=lambda x: id_order.get(x["id"], 0)
        )
    
    async def _find_similar_question(self, original: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find similar question"""
        query = select(Question).where(
            Question.is_deleted == False,
            Question.id != UUID(original["id"]),
            Question.question_type == original["question_type"],
            Question.difficulty == original["difficulty"],
            Question.review_status == "approved",
        )
        
        if original.get("knowledge_points"):
            for kp in original["knowledge_points"]:
                query = query.where(Question.knowledge_points.contains([kp]))
                break
        
        query = query.limit(5)
        result = await self.db.execute(query)
        candidates = result.scalars().all()
        
        if not candidates:
            return None
        
        selected = random.choice(list(candidates))
        
        return {
            "id": str(selected.id),
            "content": selected.content,
            "question_type": selected.question_type,
            "options": selected.options,
            "answer": selected.answer,
            "analysis": selected.analysis,
            "difficulty": selected.difficulty,
            "knowledge_points": selected.knowledge_points or [],
            "score": float(selected.score),
        }
    
    def _calculate_paper_similarity(
        self,
        questions_a: List[Dict[str, Any]],
        questions_b: List[Dict[str, Any]]
    ) -> float:
        """Calculate A/B paper similarity"""
        if len(questions_a) != len(questions_b):
            return 0.0
        
        same_count = sum(
            1 for qa, qb in zip(questions_a, questions_b)
            if qa["id"] == qb["id"]
        )
        
        same_kp = 0
        total_kp = 0
        for qa, qb in zip(questions_a, questions_b):
            kps_a = set(qa.get("knowledge_points", []))
            kps_b = set(qb.get("knowledge_points", []))
            total_kp += len(kps_a | kps_b)
            same_kp += len(kps_a & kps_b)
        
        kp_similarity = same_kp / total_kp if total_kp > 0 else 1.0
        id_similarity = same_count / len(questions_a) if questions_a else 1.0
        
        return round(0.3 * (1 - id_similarity) + 0.7 * kp_similarity, 3)
    
    async def _generate_paired_questions(
        self,
        original_questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate paired questions from original questions"""
        paired_questions = []
        for q in original_questions:
            similar = await self._find_similar_question(q)
            if similar:
                paired_questions.append(similar)
            else:
                paired_questions.append(q)
        return paired_questions
    
    async def _find_similar_replacement(
        self,
        original: Dict[str, Any],
        similar_candidates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the best similar replacement for a question"""
        if not similar_candidates:
            return None
        
        # Score candidates by similarity
        def score_candidate(candidate):
            score = 0
            # Same difficulty is important
            if candidate.get("difficulty") == original.get("difficulty"):
                score += 2
            # Same question type
            if candidate.get("question_type") == original.get("question_type"):
                score += 1
            # Overlapping knowledge points
            orig_kps = set(original.get("knowledge_points", []))
            cand_kps = set(candidate.get("knowledge_points", []))
            overlap = len(orig_kps & cand_kps)
            score += overlap
            return score
        
        best = max(similar_candidates, key=score_candidate)
        return best


class PaperService:
    """Paper service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.greedy_generator = GreedyPaperGenerator(db)
        self.diagnostic_generator = DiagnosticPaperGenerator(db)
        self.ab_generator = ABPaperGenerator(db)
    
    async def create_paper(
        self,
        data: PaperCreate,
        questions: List[Dict[str, Any]],
        creator_id: UUID
    ) -> Paper:
        """Create paper"""
        paper = Paper(
            title=data.title,
            subject=data.subject,
            grade_level=data.grade_level,
            paper_type=data.paper_type.value,
            generation_mode=data.generation_mode.value,
            constraints=data.constraints,
            question_ids=[q["id"] for q in questions],
            question_count=len(questions),
            total_score=sum(q.get("score", 5) for q in questions),
            creator_id=creator_id,
            status="draft",
            source_student_id=data.source_student_id,
            source_diagnosis=data.source_diagnosis,
        )
        
        self.db.add(paper)
        await self.db.flush()
        
        for i, q in enumerate(questions):
            pq = PaperQuestion(
                paper_id=paper.id,
                question_id=UUID(q["id"]),
                order=i + 1,
                score=float(q.get("score", 5)),
            )
            self.db.add(pq)
        
        await self.db.commit()
        await self.db.refresh(paper)
        
        return paper
    
    async def get_paper_by_id(self, paper_id: UUID) -> Optional[Paper]:
        """Get paper by ID"""
        query = select(Paper).where(Paper.id == paper_id, Paper.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_papers(
        self,
        page: int = 1,
        page_size: int = 20,
        subject: Optional[str] = None,
        paper_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Tuple[List[Paper], int]:
        """List papers"""
        query = select(Paper).where(Paper.is_deleted == False)
        
        if subject:
            query = query.where(Paper.subject == subject)
        if paper_type:
            query = query.where(Paper.paper_type == paper_type)
        if status:
            query = query.where(Paper.status == status)
        if keyword:
            query = query.where(Paper.title.contains(keyword))
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        query = query.order_by(Paper.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
    
    async def update_paper(self, paper_id: UUID, data: PaperUpdate) -> Optional[Paper]:
        """Update paper"""
        paper = await self.get_paper_by_id(paper_id)
        if not paper:
            return None
        
        if data.title is not None:
            paper.title = data.title
        if data.status is not None:
            paper.status = data.status.value
            if data.status.value == "published":
                paper.published_at = datetime.now()
        if data.constraints is not None:
            paper.constraints = data.constraints
        if data.question_ids is not None:
            paper.question_ids = [str(qid) for qid in data.question_ids]
            paper.question_count = len(data.question_ids)
        
        paper.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(paper)
        
        return paper
    
    async def delete_paper(self, paper_id: UUID) -> bool:
        """Delete paper (soft delete)"""
        paper = await self.get_paper_by_id(paper_id)
        if not paper:
            return False
        
        paper.is_deleted = True
        paper.updated_at = datetime.now()
        await self.db.commit()
        return True
    
    async def publish_paper(self, paper_id: UUID) -> Optional[Paper]:
        """Publish paper"""
        paper = await self.get_paper_by_id(paper_id)
        if not paper:
            return None
        
        paper.status = "published"
        paper.published_at = datetime.now()
        paper.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(paper)
        
        return paper
    
    async def generate_paper(
        self,
        request: PaperGenerateRequest,
        creator_id: UUID
    ) -> PaperGenerationResult:
        """Smart paper generation"""
        constraints = PaperConstraints(
            total_count=request.total_count,
            total_score=request.total_score,
            estimated_time=request.estimated_time,
            target_knowledge_points=request.target_knowledge_points,
            exclude_knowledge_points=request.exclude_knowledge_points,
            difficulty_distribution=request.difficulty_distribution,
            target_difficulty=request.target_difficulty,
            question_type_counts=request.question_type_counts,
            cognitive_levels=request.cognitive_levels,
        )
        
        return await self.greedy_generator.generate(constraints)
    
    async def generate_diagnostic_paper(
        self,
        request: DiagnosticGenerateRequest,
        creator_id: UUID
    ) -> PaperGenerationResult:
        """Diagnostic paper generation"""
        constraints = PaperConstraints(
            total_count=request.total_count,
            total_score=request.total_score,
            target_knowledge_points=request.weak_points,
        )
        
        return await self.diagnostic_generator.generate_from_diagnosis(request, constraints)
    
    async def generate_ab_papers(
        self,
        request: ABPaperRequest,
        creator_id: UUID
    ) -> Tuple[Paper, Paper, float]:
        """Generate A/B papers"""
        paper_a = await self.get_paper_by_id(request.paper_id)
        if not paper_a:
            raise ValueError("Paper not found")
        
        if paper_a.status == "published":
            raise ValueError("Cannot generate A/B for published paper")
        
        return await self.ab_generator.generate_paired_paper(paper_a, request)
    
    async def get_paper_with_questions(
        self,
        paper_id: UUID,
        include_answers: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get paper with questions"""
        paper = await self.get_paper_by_id(paper_id)
        if not paper:
            return None
        
        if paper.question_ids:
            query = select(Question).where(Question.id.in_(paper.question_ids))
            result = await self.db.execute(query)
            questions = result.scalars().all()
            
            id_order = {str(qid): i for i, qid in enumerate(paper.question_ids)}
            sorted_questions = sorted(questions, key=lambda x: id_order.get(str(x.id), 0))
            
            questions_data = []
            for q in sorted_questions:
                qdata = {
                    "id": str(q.id),
                    "order": id_order.get(str(q.id), 0) + 1,
                    "content": q.content,
                    "question_type": q.question_type,
                    "options": q.options,
                    "difficulty": q.difficulty,
                    "cognitive_level": q.cognitive_level,
                    "knowledge_points": q.knowledge_points or [],
                    "analysis": q.analysis if include_answers else None,
                }
                if include_answers:
                    qdata["answer"] = q.answer
                questions_data.append(qdata)
        else:
            questions_data = []
        
        return {
            "id": str(paper.id),
            "title": paper.title,
            "subject": paper.subject,
            "grade_level": paper.grade_level,
            "paper_type": paper.paper_type,
            "questions": questions_data,
            "total_score": float(paper.total_score),
            "estimated_time": paper.estimated_time,
            "difficulty_distribution": paper.difficulty_distribution,
            "knowledge_coverage": paper.knowledge_coverage,
            "status": paper.status,
            "created_at": paper.created_at,
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get paper statistics"""
        total_query = select(func.count()).select_from(Paper).where(Paper.is_deleted == False)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar()
        
        status_query = select(Paper.status, func.count()).where(
            Paper.is_deleted == False
        ).group_by(Paper.status)
        status_result = await self.db.execute(status_query)
        status_counts = dict(status_result.all())
        
        type_query = select(Paper.paper_type, func.count()).where(
            Paper.is_deleted == False
        ).group_by(Paper.paper_type)
        type_result = await self.db.execute(type_query)
        type_counts = dict(type_result.all())
        
        return {
            "total": total,
            "published": status_counts.get("published", 0),
            "draft": status_counts.get("draft", 0),
            "archived": status_counts.get("archived", 0),
            "by_type": type_counts,
        }
