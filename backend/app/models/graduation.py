"""
毕业管理数据模型
包含毕业审核、毕业证书、离校手续、校友管理等模型
"""
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class GraduationStatus(str, Enum):
    """毕业状态"""
    PENDING = "pending"                    # 待审核
    IN_PROGRESS = "in_progress"            # 审核中
    APPROVED = "approved"                  # 已通过
    REJECTED = "rejected"                  # 已拒绝
    GRADUATED = "graduated"                # 已毕业
    DEFERRED = "deferred"                  # 延期毕业


class AuditType(str, Enum):
    """审核类型"""
    PRELIMINARY = "preliminary"            # 资格预审
    FORMAL = "formal"                      # 正式审核
    APPEAL = "appeal"                      # 申诉审核


class CertificateStatus(str, Enum):
    """证书状态"""
    PENDING = "pending"                    # 待制作
    PRINTED = "printed"                    # 已打印
    ISSUED = "issued"                      # 已发放
    ARCHIVED = "archived"                  # 已归档
    REVOKED = "revoked"                    # 已吊销


class LeaveSchoolStatus(str, Enum):
    """离校状态"""
    PENDING = "pending"                    # 待办理
    IN_PROGRESS = "in_progress"            # 办理中
    COMPLETED = "completed"                # 已完成
    EXEMPTED = "exempted"                  # 已豁免


class CheckpointType(str, Enum):
    """离校检查点类型"""
    LIBRARY = "library"                    # 图书馆
    FINANCIAL = "financial"               # 财务结算
    DORMITORY = "dormitory"               # 宿舍
    EQUIPMENT = "equipment"                # 设备归还
    ACADEMIC = "academic"                  # 学业完成


@dataclass
class GraduationRequirement:
    """毕业要求"""
    min_total_credits: int = 160           # 最少总学分
    min_major_credits: int = 80             # 最少专业学分
    min_core_courses: int = 30             # 最少核心课程数
    min_elective_credits: int = 20         # 最少选修学分
    min_practice_credits: int = 15         # 最少实践学分
    pass_ielts: bool = False               # 是否需要雅思通过
    min_ielts_score: float = 0.0           # 最少雅思分数
    pass_graduation_design: bool = True    # 是否需要毕业设计通过


@dataclass
class GraduationAudit:
    """毕业审核记录"""
    id: int
    student_id: int
    academic_year: str                     # 学年 "2025-2026"
    semester: int                          # 学期 1或2
    audit_type: AuditType                   # 审核类型
    status: GraduationStatus                # 审核状态

    # 学业情况
    total_credits: float = 0.0            # 已获总学分
    major_credits: float = 0.0            # 专业学分
    elective_credits: float = 0.0          # 选修学分
    practice_credits: float = 0.0          # 实践学分
    completed_courses: int = 0             # 已完成课程数
    gpa: float = 0.0                        # 平均绩点

    # 毕业要求对照
    requirements: Optional[GraduationRequirement] = None

    # 审核详情
    required_courses: List[int] = field(default_factory=list)       # 必修课列表
    passed_required: List[int] = field(default_factory=list)       # 已通过必修课
    failed_required: List[int] = field(default_factory=list)        # 未通过必修课
    missing_courses: List[int] = field(default_factory=list)        # 缺失课程

    # 审核结果
    is_eligible: bool = False              # 是否符合毕业条件
    audit_comment: str = ""                # 审核意见
    auditor_id: Optional[int] = None      # 审核人ID
    audit_time: Optional[datetime] = None # 审核时间

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def check_requirements(self) -> tuple[bool, List[str]]:
        """
        检查是否满足毕业要求
        返回: (是否满足, 不满足的原因列表)
        """
        if self.requirements is None:
            return True, []

        reasons = []

        # 检查总学分
        if self.total_credits < self.requirements.min_total_credits:
            reasons.append(
                f"总学分不足: {self.total_credits}/{self.requirements.min_total_credits}"
            )

        # 检查专业学分
        if self.major_credits < self.requirements.min_major_credits:
            reasons.append(
                f"专业学分不足: {self.major_credits}/{self.requirements.min_major_credits}"
            )

        # 检查必修课
        if self.failed_required:
            reasons.append(
                f"还有{len(self.failed_required)}门必修课未通过"
            )

        # 检查选修学分
        if self.elective_credits < self.requirements.min_elective_credits:
            reasons.append(
                f"选修学分不足: {self.elective_credits}/{self.requirements.min_elective_credits}"
            )

        # 检查实践学分
        if self.practice_credits < self.requirements.min_practice_credits:
            reasons.append(
                f"实践学分不足: {self.practice_credits}/{self.requirements.min_practice_credits}"
            )

        self.is_eligible = len(reasons) == 0
        return self.is_eligible, reasons

    def get_completion_rate(self) -> float:
        """获取毕业完成度"""
        if self.requirements is None:
            return 1.0

        rate = 0.0

        # 学分完成度 (40%)
        credit_rate = min(1.0, self.total_credits / self.requirements.min_total_credits)
        rate += credit_rate * 0.4

        # 专业学分完成度 (20%)
        major_rate = min(1.0, self.major_credits / self.requirements.min_major_credits)
        rate += major_rate * 0.2

        # 必修课完成度 (25%)
        total_required = len(self.passed_required) + len(self.failed_required)
        if total_required > 0:
            required_rate = len(self.passed_required) / total_required
        else:
            required_rate = 1.0
        rate += required_rate * 0.25

        # 选修学分完成度 (10%)
        elective_rate = min(
            1.0, self.elective_credits / self.requirements.min_elective_credits
        )
        rate += elective_rate * 0.1

        # 实践学分完成度 (5%)
        practice_rate = min(
            1.0, self.practice_credits / self.requirements.min_practice_credits
        )
        rate += practice_rate * 0.05

        return round(rate, 4)


@dataclass
class GraduationCertificate:
    """毕业证书"""
    id: int
    student_id: int
    student_name: str
    certificate_number: str                  # 证书编号

    # 证书信息
    academic_year: str                     # 毕业学年
    graduation_year: int                   # 毕业年份
    graduation_month: int                 # 毕业月份
    degree_type: str = "bachelor"         # 学位类型: bachelor, master, doctor
    major: str = ""                        # 专业
    major_code: str = ""                   # 专业代码

    # 证书状态
    status: CertificateStatus = CertificateStatus.PENDING

    # 证书内容
    completion_rate: float = 0.0          # 完成度
    gpa: float = 0.0                       # 平均绩点
    honors: str = ""                       # 荣誉

    # 管理信息
    printed_by: Optional[int] = None       # 打印人
    printed_at: Optional[datetime] = None # 打印时间
    issued_by: Optional[int] = None        # 发放人
    issued_at: Optional[datetime] = None   # 发放时间

    # 归档信息
    archive_location: str = ""            # 归档位置
    archive_date: Optional[datetime] = None  # 归档日期

    # 验证信息
    qr_code: str = ""                      # 二维码
    verification_url: str = ""             # 验证网址

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_valid(self) -> bool:
        """证书是否有效"""
        return self.status not in [
            CertificateStatus.REVOKED,
            CertificateStatus.ARCHIVED
        ]

    def generate_certificate_number(self) -> str:
        """生成证书编号"""
        # 格式: 年份(4位) + 专业代码(4位) + 序号(4位)
        year = str(self.graduation_year)[-2:]  # 取后两位
        major = self.major_code[:4].zfill(4) if self.major_code else "0000"
        seq = str(self.id).zfill(4)
        return f"{year}{major}{seq}"


@dataclass
class LeaveSchoolCheckpoint:
    """离校检查点"""
    checkpoint_type: CheckpointType         # 检查点类型
    name: str                               # 检查点名称
    status: LeaveSchoolStatus = LeaveSchoolStatus.PENDING
    required: bool = True                  # 是否必须检查

    # 检查详情
    check_item: str = ""                   # 检查项目
    check_result: str = ""                 # 检查结果
    remarks: str = ""                     # 备注

    # 检查人
    checked_by: Optional[int] = None       # 检查人ID
    checked_at: Optional[datetime] = None  # 检查时间

    def complete(self, checked_by: int, result: str = "") -> bool:
        """完成检查"""
        self.status = LeaveSchoolStatus.COMPLETED
        self.checked_by = checked_by
        self.checked_at = datetime.now()
        self.check_result = result
        return True

    def exempt(self, reason: str, exempted_by: int) -> bool:
        """豁免检查"""
        self.status = LeaveSchoolStatus.EXEMPTED
        self.remarks = reason
        self.checked_by = exempted_by
        self.checked_at = datetime.now()
        return True


@dataclass
class LeaveSchoolRecord:
    """离校记录"""
    id: int
    student_id: int
    student_name: str
    academic_year: str                     # 学年
    semester: int                          # 学期

    # 离校类型
    leave_type: str = "graduation"         # 离校类型: graduation, transfer, dropout
    graduation_date: Optional[datetime] = None  # 实际离校日期

    # 检查点列表
    checkpoints: List[LeaveSchoolCheckpoint] = field(default_factory=list)

    # 总体状态
    status: LeaveSchoolStatus = LeaveSchoolStatus.PENDING

    # 办理人
    processed_by: Optional[int] = None   # 办理人
    processed_at: Optional[datetime] = None  # 办理时间

    # 备注
    remarks: str = ""

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_checkpoint(self, checkpoint: LeaveSchoolCheckpoint) -> None:
        """添加检查点"""
        self.checkpoints.append(checkpoint)

    def get_pending_checkpoints(self) -> List[LeaveSchoolCheckpoint]:
        """获取待办理的检查点"""
        return [
            c for c in self.checkpoints
            if c.status == LeaveSchoolStatus.PENDING and c.required
        ]

    def get_completed_checkpoints(self) -> List[LeaveSchoolCheckpoint]:
        """获取已完成的检查点"""
        return [
            c for c in self.checkpoints
            if c.status in [
                LeaveSchoolStatus.COMPLETED,
                LeaveSchoolStatus.EXEMPTED
            ]
        ]

    def is_completed(self) -> bool:
        """是否完成所有离校手续"""
        required_checkpoints = [c for c in self.checkpoints if c.required]
        if not required_checkpoints:
            return True

        return all(
            c.status in [LeaveSchoolStatus.COMPLETED, LeaveSchoolStatus.EXEMPTED]
            for c in required_checkpoints
        )

    def get_completion_rate(self) -> float:
        """获取办理进度"""
        if not self.checkpoints:
            return 1.0 if self.status == LeaveSchoolStatus.COMPLETED else 0.0

        required = [c for c in self.checkpoints if c.required]
        if not required:
            return 1.0

        completed = [
            c for c in required
            if c.status in [LeaveSchoolStatus.COMPLETED, LeaveSchoolStatus.EXEMPTED]
        ]
        return len(completed) / len(required)


@dataclass
class AlumniRecord:
    """校友记录"""
    id: int
    student_id: int

    # 基本信息
    name: str
    gender: str = ""
    birth_date: Optional[datetime] = None
    id_card: str = ""                      # 身份证号
    political_status: str = ""            # 政治面貌

    # 联系方式
    phone: str = ""
    email: str = ""
    wechat: str = ""
    qq: str = ""
    address: str = ""                      # 通讯地址

    # 教育信息
    admission_year: int = 0               # 入学年份
    graduation_year: int = 0              # 毕业年份
    major: str = ""
    degree: str = ""                       # 学位
    student_class: str = ""               # 班级

    # 校友信息
    employer: str = ""                    # 工作单位
    position: str = ""                     # 职位
    industry: str = ""                     # 行业
    annual_income: str = ""               # 年薪范围
    employment_status: str = "employed"   # 就业状态

    # 校友会信息
    alumni_association: bool = False      # 是否加入校友会
    alumni_level: str = "normal"          # 校友级别: normal, silver, gold, platinum
    contributions: float = 0.0            # 贡献值

    # 社交信息
    linkedin: str = ""
    personal_website: str = ""
    blog: str = ""

    # 其他
    remarks: str = ""
    is_active: bool = True
    last_contact: Optional[datetime] = None  # 最后联系时间

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_contact_info(self, phone: str = "", email: str = "") -> bool:
        """更新联系方式"""
        if phone:
            self.phone = phone
        if email:
            self.email = email
        self.updated_at = datetime.now()
        return True

    def add_contribution(self, amount: float, source: str = "") -> float:
        """添加贡献值"""
        self.contributions += amount

        # 根据贡献值更新级别
        if self.contributions >= 10000:
            self.alumni_level = "platinum"
        elif self.contributions >= 5000:
            self.alumni_level = "gold"
        elif self.contributions >= 1000:
            self.alumni_level = "silver"

        self.updated_at = datetime.now()
        return self.contributions


@dataclass
class GraduationStatistics:
    """毕业统计"""
    academic_year: str                     # 学年
    semester: int                          # 学期

    # 数量统计
    total_students: int = 0                # 应毕业人数
    graduated_count: int = 0               # 已毕业人数
    pending_count: int = 0                 # 待审核人数
    deferred_count: int = 0                # 延期人数

    # 学位统计
    bachelor_count: int = 0               # 学士学位
    master_count: int = 0                  # 硕士学位
    doctor_count: int = 0                  # 博士学位

    # 成绩统计
    average_gpa: float = 0.0               # 平均绩点
    highest_gpa: float = 0.0                # 最高绩点
    lowest_gpa: float = 0.0                # 最低绩点

    # 完成度统计
    average_completion_rate: float = 0.0   # 平均完成度
    full_completion_count: int = 0         # 完全达标人数

    # 离校统计
    leave_school_completed: int = 0       # 已完成离校
    leave_school_pending: int = 0          # 待办理离校

    def get_graduation_rate(self) -> float:
        """计算毕业率"""
        if self.total_students == 0:
            return 0.0
        return round(self.graduated_count / self.total_students, 4)


@dataclass
class GraduationReport:
    """毕业报告"""
    audit_id: int
    student_id: int
    student_name: str

    # 学业概况
    total_credits: float
    major_credits: float
    elective_credits: float
    practice_credits: float
    gpa: float

    # 毕业条件
    is_eligible: bool
    completion_rate: float
    missing_requirements: List[str] = field(default_factory=list)

    # 建议
    suggestions: List[str] = field(default_factory=list)

    # 生成信息
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "system"
