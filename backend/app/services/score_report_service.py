"""
成绩报表服务
提供学生成绩分析、班级统计、科目分析、成绩导出等功能
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ReportType(str, Enum):
    """报表类型"""
    STUDENT = "student"              # 学生成绩单
    CLASS = "class"                   # 班级成绩统计
    SUBJECT = "subject"              # 科目分析
    EXAM = "exam"                    # 考试分析
    TREND = "trend"                  # 成绩趋势
    COMPARISON = "comparison"       # 对比分析


class GradeLevel(str, Enum):
    """成绩等级"""
    EXCELLENT = "A"                 # 优秀 (90-100)
    GOOD = "B"                       # 良好 (80-89)
    AVERAGE = "C"                    # 中等 (70-79)
    PASS = "D"                       # 及格 (60-69)
    FAIL = "F"                       # 不及格 (<60)


class ScoreDistribution:
    """分数分布"""

    def __init__(self):
        self.bins = {
            "0-59": 0,
            "60-69": 0,
            "70-79": 0,
            "80-89": 0,
            "90-100": 0
        }
        self.total = 0

    def add_score(self, score: float) -> None:
        """添加分数"""
        self.total += 1
        if score < 60:
            self.bins["0-59"] += 1
        elif score < 70:
            self.bins["60-69"] += 1
        elif score < 80:
            self.bins["70-79"] += 1
        elif score < 90:
            self.bins["80-89"] += 1
        else:
            self.bins["90-100"] += 1

    def get_distribution(self) -> Dict[str, float]:
        """获取分布比例"""
        if self.total == 0:
            return {k: 0.0 for k in self.bins.keys()}
        return {k: round(v / self.total, 4) for k, v in self.bins.items()}

    def get_pass_rate(self) -> float:
        """计算及格率"""
        if self.total == 0:
            return 0.0
        passed = sum(self.bins[k] for k in ["60-69", "70-79", "80-89", "90-100"])
        return round(passed / self.total, 4)

    def get_average_score(self) -> float:
        """计算平均分（需要原始分数）"""
        # 这里返回0，实际使用时需要原始分数列表
        return 0.0


@dataclass
class StudentScore:
    """学生成绩"""
    student_id: int
    student_name: str
    exam_id: int
    subject_id: int
    subject_name: str
    score: float
    full_score: float = 100.0
    rank: int = 0
    grade_level: GradeLevel = GradeLevel.FAIL

    def get_percentile(self) -> float:
        """获取百分位"""
        return round((self.score / self.full_score) * 100, 2)

    def is_pass(self) -> bool:
        """是否及格"""
        return self.score >= 60


@dataclass
class StudentReport:
    """学生成绩报表"""
    student_id: int
    student_name: str
    academic_year: str
    semester: int

    # 基本信息
    total_courses: int = 0
    passed_courses: int = 0
    failed_courses: int = 0

    # 成绩统计
    total_score: float = 0.0           # 总分
    average_score: float = 0.0         # 平均分
    highest_score: float = 0.0         # 最高分
    lowest_score: float = 0.0           # 最低分
    gpa: float = 0.0                    # 绩点

    # 等级分布
    excellent_count: int = 0            # 优秀数
    good_count: int = 0                 # 良好数
    average_count: int = 0              # 中等数
    pass_count: int = 0                  # 及格数
    fail_count: int = 0                  # 不及格数

    # 排名
    class_rank: int = 0                 # 班级排名
    grade_rank: int = 0                 # 年级排名

    # 科目明细
    subject_scores: List[StudentScore] = field(default_factory=list)

    # 时间戳
    generated_at: datetime = field(default_factory=datetime.now)

    def get_pass_rate(self) -> float:
        """计算及格率"""
        if self.total_courses == 0:
            return 0.0
        return round(self.passed_courses / self.total_courses, 4)

    def get_completion_rate(self) -> float:
        """完成率"""
        if self.total_courses == 0:
            return 0.0
        return round((self.total_courses - self.failed_courses) / self.total_courses, 4)


@dataclass
class ClassReport:
    """班级成绩报表"""
    class_id: int
    class_name: str
    academic_year: str
    semester: int

    # 基本信息
    total_students: int = 0
    total_exams: int = 0

    # 成绩统计
    class_average: float = 0.0         # 班级平均分
    highest_score: float = 0.0         # 最高分
    lowest_score: float = 0.0           # 最低分
    score_std: float = 0.0              # 标准差

    # 及格率相关
    pass_count: int = 0                # 及格人数
    pass_rate: float = 0.0              # 及格率
    excellent_count: int = 0             # 优秀人数
    excellent_rate: float = 0.0         # 优秀率

    # 科目分析
    subject_averages: Dict[str, float] = field(default_factory=dict)  # 科目平均分
    subject_pass_rates: Dict[str, float] = field(default_factory=dict)  # 科目及格率

    # 分数分布
    score_distribution: Dict[str, float] = field(default_factory=dict)

    # 排名
    class_rank_list: List[Dict] = field(default_factory=list)  # 班级排名

    # 时间戳
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SubjectReport:
    """科目成绩报表"""
    subject_id: int
    subject_name: str
    academic_year: str
    semester: int

    # 基本信息
    total_students: int = 0
    total_exams: int = 0

    # 成绩统计
    subject_average: float = 0.0        # 科目平均分
    highest_score: float = 0.0          # 最高分
    lowest_score: float = 0.0           # 最低分
    median_score: float = 0.0           # 中位数
    score_std: float = 0.0              # 标准差

    # 及格率
    pass_count: int = 0
    pass_rate: float = 0.0

    # 等级分布
    excellent_rate: float = 0.0
    good_rate: float = 0.0
    average_rate: float = 0.0

    # 分数分布
    score_distribution: Dict[str, float] = field(default_factory=dict)

    # 教师分析
    teacher_id: Optional[int] = None
    teacher_name: str = ""

    # 时间戳
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExamReport:
    """考试分析报表"""
    exam_id: int
    exam_name: str
    academic_year: str
    semester: int
    exam_date: str

    # 基本信息
    total_students: int = 0
    total_subjects: int = 0

    # 整体统计
    overall_average: float = 0.0
    highest_score: float = 0.0
    lowest_score: float = 0.0
    score_std: float = 0.0

    # 及格率
    pass_count: int = 0
    pass_rate: float = 0.0

    # 分数分布
    score_distribution: Dict[str, float] = field(default_factory=dict)

    # 科目分析
    subject_analysis: List[Dict] = field(default_factory=list)

    # 问题分析
    difficulty_index: float = 0.0       # 难度指数
    discrimination_index: float = 0.0    # 区分度

    # 时间戳
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrendReport:
    """成绩趋势报表"""
    student_id: int
    student_name: str
    academic_year: str

    # 趋势数据
    semester_scores: List[Dict] = field(default_factory=list)  # 各学期成绩
    subject_trends: Dict[str, List[float]] = field(default_factory=dict)  # 科目趋势

    # 趋势分析
    overall_trend: str = "stable"        # 上升/下降/稳定
    improvement_rate: float = 0.0        # 进步率
    volatility: float = 0.0              # 波动性

    # 预测
    predicted_next: float = 0.0          # 预测下次成绩

    # 时间戳
    generated_at: datetime = field(default_factory=datetime.now)


# ==================== 服务实现 ====================

class ScoreReportService:
    """成绩报表服务"""

    def __init__(self):
        self._student_scores: Dict[int, List[StudentScore]] = defaultdict(list)
        self._class_reports: Dict[int, ClassReport] = {}
        self._subject_reports: Dict[int, SubjectReport] = {}
        self._exam_reports: Dict[int, ExamReport] = {}

    # ==================== 学生成绩录入 ====================

    def add_student_score(
        self,
        student_id: int,
        student_name: str,
        exam_id: int,
        subject_id: int,
        subject_name: str,
        score: float,
        full_score: float = 100.0
    ) -> StudentScore:
        """添加学生成绩"""
        # 计算等级
        percentile = (score / full_score) * 100
        if percentile >= 90:
            grade_level = GradeLevel.EXCELLENT
        elif percentile >= 80:
            grade_level = GradeLevel.GOOD
        elif percentile >= 70:
            grade_level = GradeLevel.AVERAGE
        elif percentile >= 60:
            grade_level = GradeLevel.PASS
        else:
            grade_level = GradeLevel.FAIL

        student_score = StudentScore(
            student_id=student_id,
            student_name=student_name,
            exam_id=exam_id,
            subject_id=subject_id,
            subject_name=subject_name,
            score=score,
            full_score=full_score,
            grade_level=grade_level
        )

        self._student_scores[student_id].append(student_score)
        return student_score

    def get_student_scores(
        self,
        student_id: int,
        academic_year: Optional[str] = None
    ) -> List[StudentScore]:
        """获取学生成绩列表"""
        scores = self._student_scores.get(student_id, [])
        if academic_year:
            # 简化过滤逻辑
            pass
        return scores

    # ==================== 学生报表生成 ====================

    def generate_student_report(
        self,
        student_id: int,
        student_name: str,
        academic_year: str,
        semester: int
    ) -> StudentReport:
        """生成学生成绩报表"""
        scores = self.get_student_scores(student_id)

        if not scores:
            return StudentReport(
                student_id=student_id,
                student_name=student_name,
                academic_year=academic_year,
                semester=semester
            )

        # 统计
        total_score = sum(s.score for s in scores)
        average_score = total_score / len(scores)
        highest_score = max(s.score for s in scores)
        lowest_score = min(s.score for s in scores)

        # 等级统计
        excellent_count = sum(1 for s in scores if s.grade_level == GradeLevel.EXCELLENT)
        good_count = sum(1 for s in scores if s.grade_level == GradeLevel.GOOD)
        average_count = sum(1 for s in scores if s.grade_level == GradeLevel.AVERAGE)
        pass_count = sum(1 for s in scores if s.grade_level == GradeLevel.PASS)
        fail_count = sum(1 for s in scores if s.grade_level == GradeLevel.FAIL)

        # GPA计算（简化版）
        gpa = self._calculate_gpa(scores)

        report = StudentReport(
            student_id=student_id,
            student_name=student_name,
            academic_year=academic_year,
            semester=semester,
            total_courses=len(scores),
            passed_courses=len(scores) - fail_count,
            failed_courses=fail_count,
            total_score=total_score,
            average_score=round(average_score, 2),
            highest_score=highest_score,
            lowest_score=lowest_score,
            gpa=round(gpa, 2),
            excellent_count=excellent_count,
            good_count=good_count,
            average_count=average_count,
            pass_count=pass_count,
            fail_count=fail_count,
            subject_scores=scores
        )

        return report

    def _calculate_gpa(self, scores: List[StudentScore]) -> float:
        """计算GPA"""
        if not scores:
            return 0.0

        grade_points = {
            GradeLevel.EXCELLENT: 4.0,
            GradeLevel.GOOD: 3.0,
            GradeLevel.AVERAGE: 2.0,
            GradeLevel.PASS: 1.0,
            GradeLevel.FAIL: 0.0
        }

        total_points = sum(grade_points[s.grade_level] for s in scores)
        return total_points / len(scores)

    # ==================== 班级报表生成 ====================

    def generate_class_report(
        self,
        class_id: int,
        class_name: str,
        academic_year: str,
        semester: int,
        student_ids: List[int]
    ) -> ClassReport:
        """生成班级成绩报表"""
        all_scores: List[StudentScore] = []
        for sid in student_ids:
            all_scores.extend(self.get_student_scores(sid))

        if not all_scores:
            return ClassReport(
                class_id=class_id,
                class_name=class_name,
                academic_year=academic_year,
                semester=semester
            )

        # 基本统计
        total_students = len(student_ids)
        scores_list = [s.score for s in all_scores]
        class_average = sum(scores_list) / len(scores_list)
        highest_score = max(scores_list)
        lowest_score = min(scores_list)

        # 标准差
        variance = sum((s - class_average) ** 2 for s in scores_list) / len(scores_list)
        score_std = variance ** 0.5

        # 及格率
        pass_count = sum(1 for s in all_scores if s.is_pass())
        pass_rate = pass_count / len(all_scores) if all_scores else 0.0

        # 优秀率
        excellent_count = sum(1 for s in all_scores if s.grade_level == GradeLevel.EXCELLENT)
        excellent_rate = excellent_count / len(all_scores) if all_scores else 0.0

        # 分数分布
        distribution = ScoreDistribution()
        for s in all_scores:
            distribution.add_score(s.score)
        score_distribution = distribution.get_distribution()

        # 科目平均分
        subject_averages: Dict[str, float] = defaultdict(list)
        for s in all_scores:
            subject_averages[s.subject_name].append(s.score)

        subject_avg_result = {
            k: round(sum(v) / len(v), 2) for k, v in subject_averages.items()
        }

        report = ClassReport(
            class_id=class_id,
            class_name=class_name,
            academic_year=academic_year,
            semester=semester,
            total_students=total_students,
            class_average=round(class_average, 2),
            highest_score=highest_score,
            lowest_score=lowest_score,
            score_std=round(score_std, 2),
            pass_count=pass_count,
            pass_rate=round(pass_rate, 4),
            excellent_count=excellent_count,
            excellent_rate=round(excellent_rate, 4),
            subject_averages=subject_avg_result,
            score_distribution=score_distribution
        )

        self._class_reports[class_id] = report
        return report

    # ==================== 科目报表生成 ====================

    def generate_subject_report(
        self,
        subject_id: int,
        subject_name: str,
        academic_year: str,
        semester: int
    ) -> SubjectReport:
        """生成科目成绩报表"""
        all_scores: List[StudentScore] = []

        for scores in self._student_scores.values():
            for s in scores:
                if s.subject_id == subject_id:
                    all_scores.append(s)

        if not all_scores:
            return SubjectReport(
                subject_id=subject_id,
                subject_name=subject_name,
                academic_year=academic_year,
                semester=semester
            )

        # 基本统计
        scores_list = [s.score for s in all_scores]
        subject_average = sum(scores_list) / len(scores_list)
        highest_score = max(scores_list)
        lowest_score = min(scores_list)

        # 中位数
        sorted_scores = sorted(scores_list)
        n = len(sorted_scores)
        if n % 2 == 0:
            median_score = (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
        else:
            median_score = sorted_scores[n // 2]

        # 标准差
        variance = sum((s - subject_average) ** 2 for s in scores_list) / len(scores_list)
        score_std = variance ** 0.5

        # 及格率
        pass_count = sum(1 for s in all_scores if s.is_pass())
        pass_rate = pass_count / len(all_scores)

        # 等级分布
        excellent_count = sum(1 for s in all_scores if s.grade_level == GradeLevel.EXCELLENT)
        good_count = sum(1 for s in all_scores if s.grade_level == GradeLevel.GOOD)
        average_count = sum(1 for s in all_scores if s.grade_level == GradeLevel.AVERAGE)

        excellent_rate = excellent_count / len(all_scores)
        good_rate = good_count / len(all_scores)
        average_rate = average_count / len(all_scores)

        # 分数分布
        distribution = ScoreDistribution()
        for s in all_scores:
            distribution.add_score(s.score)
        score_distribution = distribution.get_distribution()

        report = SubjectReport(
            subject_id=subject_id,
            subject_name=subject_name,
            academic_year=academic_year,
            semester=semester,
            total_students=len(all_scores),
            subject_average=round(subject_average, 2),
            highest_score=highest_score,
            lowest_score=lowest_score,
            median_score=round(median_score, 2),
            score_std=round(score_std, 2),
            pass_count=pass_count,
            pass_rate=round(pass_rate, 4),
            excellent_rate=round(excellent_rate, 4),
            good_rate=round(good_rate, 4),
            average_rate=round(average_rate, 4),
            score_distribution=score_distribution
        )

        self._subject_reports[subject_id] = report
        return report

    # ==================== 考试报表生成 ====================

    def generate_exam_report(
        self,
        exam_id: int,
        exam_name: str,
        academic_year: str,
        semester: int,
        exam_date: str
    ) -> ExamReport:
        """生成考试分析报表"""
        all_scores: List[StudentScore] = []

        for scores in self._student_scores.values():
            for s in scores:
                if s.exam_id == exam_id:
                    all_scores.append(s)

        if not all_scores:
            return ExamReport(
                exam_id=exam_id,
                exam_name=exam_name,
                academic_year=academic_year,
                semester=semester,
                exam_date=exam_date
            )

        # 基本统计
        scores_list = [s.score for s in all_scores]
        overall_average = sum(scores_list) / len(scores_list)
        highest_score = max(scores_list)
        lowest_score = min(scores_list)

        # 标准差
        variance = sum((s - overall_average) ** 2 for s in scores_list) / len(scores_list)
        score_std = variance ** 0.5

        # 及格率
        pass_count = sum(1 for s in all_scores if s.is_pass())
        pass_rate = pass_count / len(all_scores)

        # 分数分布
        distribution = ScoreDistribution()
        for s in all_scores:
            distribution.add_score(s.score)
        score_distribution = distribution.get_distribution()

        # 科目分析
        subject_scores: Dict[str, List[float]] = defaultdict(list)
        for s in all_scores:
            subject_scores[s.subject_name].append(s.score)

        subject_analysis = []
        for subject_name, scores in subject_scores.items():
            avg = sum(scores) / len(scores)
            pass_cnt = sum(1 for sc in scores if sc >= 60)
            subject_analysis.append({
                "subject_name": subject_name,
                "average": round(avg, 2),
                "pass_rate": round(pass_cnt / len(scores), 4),
                "total_students": len(scores)
            })

        # 难度指数（简化：平均分/满分）
        difficulty_index = overall_average / 100.0

        # 区分度（简化：最高分-最低分）
        discrimination_index = (highest_score - lowest_score) / 100.0

        report = ExamReport(
            exam_id=exam_id,
            exam_name=exam_name,
            academic_year=academic_year,
            semester=semester,
            exam_date=exam_date,
            total_students=len(set(s.student_id for s in all_scores)),
            total_subjects=len(subject_scores),
            overall_average=round(overall_average, 2),
            highest_score=highest_score,
            lowest_score=lowest_score,
            score_std=round(score_std, 2),
            pass_count=pass_count,
            pass_rate=round(pass_rate, 4),
            score_distribution=score_distribution,
            subject_analysis=subject_analysis,
            difficulty_index=round(difficulty_index, 4),
            discrimination_index=round(discrimination_index, 4)
        )

        self._exam_reports[exam_id] = report
        return report

    # ==================== 成绩趋势分析 ====================

    def generate_trend_report(
        self,
        student_id: int,
        student_name: str,
        academic_year: str
    ) -> TrendReport:
        """生成成绩趋势报表"""
        scores = self.get_student_scores(student_id)

        # 按学期分组（简化）
        semester_scores: Dict[int, List[float]] = defaultdict(list)
        for s in scores:
            # 简化：假设semester可以从某个地方获取
            semester_scores[1].append(s.score)

        semester_trend = []
        prev_avg = None
        for sem, sc_list in sorted(semester_scores.items()):
            avg = sum(sc_list) / len(sc_list)
            semester_trend.append({
                "semester": sem,
                "average": round(avg, 2)
            })
            if prev_avg is not None:
                if avg > prev_avg:
                    trend = "上升"
                elif avg < prev_avg:
                    trend = "下降"
                else:
                    trend = "稳定"
            prev_avg = avg

        # 整体趋势判断
        if len(semester_trend) >= 2:
            first_avg = semester_trend[0]["average"]
            last_avg = semester_trend[-1]["average"]
            if last_avg > first_avg + 5:
                overall_trend = "上升"
            elif last_avg < first_avg - 5:
                overall_trend = "下降"
            else:
                overall_trend = "稳定"
        else:
            overall_trend = "stable"

        # 进步率
        if len(semester_trend) >= 2:
            first = semester_trend[0]["average"]
            last = semester_trend[-1]["average"]
            improvement_rate = ((last - first) / first * 100) if first > 0 else 0
        else:
            improvement_rate = 0.0

        # 预测下次成绩（线性回归简化）
        if len(semester_trend) >= 2:
            x = list(range(len(semester_trend)))
            y = [t["average"] for t in semester_trend]
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(xi * yi for xi, yi in zip(x, y))
            sum_x2 = sum(xi ** 2 for xi in x)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
            intercept = (sum_y - slope * sum_x) / n

            predicted_next = slope * n + intercept  # 预测下学期
        else:
            predicted_next = semester_trend[0]["average"] if semester_trend else 0

        report = TrendReport(
            student_id=student_id,
            student_name=student_name,
            academic_year=academic_year,
            semester_scores=semester_trend,
            overall_trend=overall_trend,
            improvement_rate=round(improvement_rate, 2),
            predicted_next=round(predicted_next, 2)
        )

        return report

    # ==================== 对比分析 ====================

    def compare_students(
        self,
        student_ids: List[int],
        academic_year: str,
        semester: int
    ) -> List[Dict[str, Any]]:
        """对比分析多个学生"""
        results = []

        for sid in student_ids:
            scores = self.get_student_scores(sid)
            if not scores:
                continue

            avg_score = sum(s.score for s in scores) / len(scores)
            pass_count = sum(1 for s in scores if s.is_pass())
            pass_rate = pass_count / len(scores)

            results.append({
                "student_id": sid,
                "average_score": round(avg_score, 2),
                "pass_rate": round(pass_rate, 4),
                "total_courses": len(scores)
            })

        # 排序
        results.sort(key=lambda x: x["average_score"], reverse=True)

        # 添加排名
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results

    def compare_classes(
        self,
        class_ids: List[int],
        academic_year: str,
        semester: int
    ) -> List[Dict[str, Any]]:
        """对比分析多个班级"""
        results = []

        for cid in class_ids:
            report = self._class_reports.get(cid)
            if not report:
                continue

            results.append({
                "class_id": cid,
                "class_name": report.class_name,
                "average_score": report.class_average,
                "pass_rate": report.pass_rate,
                "excellent_rate": report.excellent_rate,
                "total_students": report.total_students
            })

        # 排序
        results.sort(key=lambda x: x["average_score"], reverse=True)

        # 添加排名
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results

    # ==================== 数据导出 ====================

    def export_student_report(
        self,
        student_id: int,
        academic_year: str,
        semester: int,
        format: str = "json"
    ) -> Dict[str, Any]:
        """导出学生成绩报表"""
        report = self.generate_student_report(
            student_id, "", academic_year, semester
        )

        if format == "json":
            return {
                "student_id": report.student_id,
                "student_name": report.student_name,
                "academic_year": report.academic_year,
                "semester": report.semester,
                "total_courses": report.total_courses,
                "passed_courses": report.passed_courses,
                "average_score": report.average_score,
                "gpa": report.gpa,
                "pass_rate": report.get_pass_rate(),
                "grades": [
                    {
                        "subject": s.subject_name,
                        "score": s.score,
                        "grade": s.grade_level.value
                    }
                    for s in report.subject_scores
                ]
            }
        else:
            # 其他格式可以扩展
            return {"error": "Unsupported format"}


# 创建全局服务实例
score_report_service = ScoreReportService()
