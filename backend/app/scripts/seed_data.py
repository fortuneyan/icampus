"""
智慧校园 - 种子数据脚本
========================
生成范围：
  - 年级：小学1-6年级 + 初中1-3年级 + 高中1-3年级 = 12个年级
  - 班级：每年级4个班 = 48个班
  - 学生：每班30人 = 1440人，小学入学年龄一律6岁
  - 课程：小学到高中全部国家标准课程
  - 教师：每课程至少2位老师
  - 部门/角色：基础组织架构

使用方式：
  cd backend
  python -m app.scripts.seed_data
"""

import asyncio
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# 确保项目根目录在 sys.path
backend_dir = str(Path(__file__).resolve().parents[2])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, Base, engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.role import Role
from app.models.grade_model import Grade
from app.models.class_model import Class
from app.models.student import Student
from app.models.course import Course
from app.models.teacher_profile import TeacherProfile


# ============================================================
# 常量定义
# ============================================================

ACADEMIC_YEAR = "2025-2026"
SEMESTER = "1"  # 第一学期
DEFAULT_PASSWORD = "teacher123"

# 12个年级定义：(名称, 编码, 年级层级, 学段, 义务教育年限)
GRADES = [
    ("一年级", "G01", 1, "primary", 1),
    ("二年级", "G02", 2, "primary", 2),
    ("三年级", "G03", 3, "primary", 3),
    ("四年级", "G04", 4, "primary", 4),
    ("五年级", "G05", 5, "primary", 5),
    ("六年级", "G06", 6, "primary", 6),
    ("七年级", "G07", 7, "junior", 7),
    ("八年级", "G08", 8, "junior", 8),
    ("九年级", "G09", 9, "junior", 9),
    ("高一", "G10", 10, "senior", 10),
    ("高二", "G11", 11, "senior", 11),
    ("高三", "G12", 12, "senior", 12),
]

# 班级后缀
CLASS_SUFFIXES = ["1班", "2班", "3班", "4班"]

# ============================================================
# 国家标准课程定义
# 格式：(课程名, 编码前缀, 类别, 学分, 课时/周, 考试类型, 适用学段列表)
# 学段: primary=小学, junior=初中, senior=高中
# ============================================================

COURSES_SPEC = [
    # ─── 小学课程 ───
    ("语文",       "CHN", "文科", 0, 8, "考试", ["primary"]),
    ("数学",       "MATH", "理科", 0, 5, "考试", ["primary"]),
    ("英语",       "ENG",  "文科", 0, 3, "考试", ["primary"]),
    ("科学",       "SCI",  "理科", 0, 2, "考查", ["primary"]),
    ("道德与法治", "MOR",  "文科", 0, 2, "考查", ["primary"]),
    ("体育与健康", "PE",   "体艺", 0, 3, "考查", ["primary"]),
    ("音乐",       "MUS",  "体艺", 0, 2, "考查", ["primary"]),
    ("美术",       "ART",  "体艺", 0, 2, "考查", ["primary"]),
    ("信息技术",   "IT",   "理科", 0, 1, "考查", ["primary"]),
    ("劳动",       "LAB",  "综合", 0, 1, "考查", ["primary"]),
    ("综合实践",   "PRC",  "综合", 0, 1, "考查", ["primary"]),

    # ─── 初中课程 ───
    ("语文",       "CHN", "文科", 0, 6, "考试", ["junior"]),
    ("数学",       "MATH", "理科", 0, 5, "考试", ["junior"]),
    ("英语",       "ENG",  "文科", 0, 4, "考试", ["junior"]),
    ("物理",       "PHY",  "理科", 0, 3, "考试", ["junior"]),
    ("化学",       "CHEM", "理科", 0, 3, "考试", ["junior"]),
    ("生物",       "BIO",  "理科", 0, 2, "考试", ["junior"]),
    ("历史",       "HIS",  "文科", 0, 2, "考试", ["junior"]),
    ("地理",       "GEO",  "文科", 0, 2, "考试", ["junior"]),
    ("道德与法治", "MOR",  "文科", 0, 2, "考试", ["junior"]),
    ("体育与健康", "PE",   "体艺", 0, 3, "考查", ["junior"]),
    ("音乐",       "MUS",  "体艺", 0, 1, "考查", ["junior"]),
    ("美术",       "ART",  "体艺", 0, 1, "考查", ["junior"]),
    ("信息技术",   "IT",   "理科", 0, 1, "考查", ["junior"]),
    ("劳动",       "LAB",  "综合", 0, 1, "考查", ["junior"]),

    # ─── 高中课程（按新课标） ───
    # 必修
    ("语文",           "CHN",  "文科", 8, 4, "考试", ["senior"]),
    ("数学",           "MATH", "理科", 8, 4, "考试", ["senior"]),
    ("英语",           "ENG",  "文科", 6, 4, "考试", ["senior"]),
    ("物理",           "PHY",  "理科", 6, 3, "考试", ["senior"]),
    ("化学",           "CHEM", "理科", 4, 3, "考试", ["senior"]),
    ("生物",           "BIO",  "理科", 4, 2, "考试", ["senior"]),
    ("历史",           "HIS",  "文科", 4, 2, "考试", ["senior"]),
    ("地理",           "GEO",  "文科", 4, 2, "考试", ["senior"]),
    ("思想政治",       "POL",  "文科", 6, 2, "考试", ["senior"]),
    ("体育与健康",     "PE",   "体艺", 6, 2, "考查", ["senior"]),
    ("信息技术",       "IT",   "理科", 3, 2, "考查", ["senior"]),
    ("通用技术",       "TECH", "理科", 3, 1, "考查", ["senior"]),
    ("音乐",           "MUS",  "体艺", 3, 1, "考查", ["senior"]),
    ("美术",           "ART",  "体艺", 3, 1, "考查", ["senior"]),
    # 选择性必修 / 选修
    ("物理选择性必修", "PHY-S", "理科", 4, 2, "考试", ["senior"]),
    ("化学选择性必修", "CHEM-S", "理科", 4, 2, "考试", ["senior"]),
    ("生物选择性必修", "BIO-S",  "理科", 3, 2, "考试", ["senior"]),
    ("历史选择性必修", "HIS-S",  "文科", 3, 2, "考试", ["senior"]),
    ("地理选择性必修", "GEO-S",  "文科", 3, 2, "考试", ["senior"]),
]

# 部门定义
DEPARTMENTS = [
    ("校办",   "SCH-OFFICE", "学校行政办公室", 1),
    ("教务处", "ACAD",       "教学管理",       1),
    ("学工处", "STU-AFF",    "学生事务管理",   1),
    ("语文组", "CHN-DEPT",   "语文学科组",     2),
    ("数学组", "MATH-DEPT",  "数学学科组",     2),
    ("英语组", "ENG-DEPT",   "英语学科组",     2),
    ("理科组", "SCI-DEPT",   "物理/化学/生物/科学", 2),
    ("文科组", "HUM-DEPT",   "历史/地理/道法/政治", 2),
    ("体艺组", "PE-ART-DEPT","体育/音乐/美术",  2),
    ("技术组", "TECH-DEPT",  "信息技术/通用技术/劳动", 2),
    ("综合组", "COMP-DEPT",  "综合实践",       2),
]

# 角色定义
ROLES = [
    ("admin",     "系统管理员", "系统最高权限", 1),
    ("principal", "校长",       "学校管理层",   2),
    ("director",  "教务主任",   "教务管理",     3),
    ("teacher",   "教师",       "教学人员",     4),
    ("student",   "学生",       "在校生",       5),
    ("parent",    "家长",       "学生监护人",   6),
]

# 姓氏库（常见姓氏，按频率加权）
SURNAMES = [
    "王","李","张","刘","陈","杨","黄","赵","周","吴",
    "徐","孙","马","胡","朱","郭","何","林","罗","高",
    "梁","郑","谢","宋","唐","韩","曹","许","邓","冯",
    "萧","程","蔡","彭","潘","袁","于","董","余","苏",
    "叶","吕","魏","蒋","田","杜","丁","沈","任","姚",
]

# 名字库（双字名）
GIVEN_NAMES_MALE = [
    "伟","强","磊","军","勇","杰","涛","明","辉","鑫",
    "浩","宇","博","文","志","建","国","俊","峰","海",
    "天","飞","鹏","超","龙","刚","毅","坤","阳","亮",
    "晨","瑞","泽","嘉","睿","恒","逸","轩","铭","昊",
    "子涵","子轩","浩然","宇轩","皓轩","博文","天佑","思远","嘉豪","梓豪",
    "一鸣","泽宇","梓轩","宇航","文博","子墨","铭泽","俊杰","致远","嘉瑞",
]

GIVEN_NAMES_FEMALE = [
    "芳","秀英","敏","静","丽","娟","艳","燕","玲","桂英",
    "雪","慧","婷","萍","红","兰","霞","倩","琳","莉",
    "雅","颖","欣","梦","瑶","蕾","薇","思","佳","怡",
    "语嫣","欣怡","思涵","梦瑶","雨婷","诗涵","梓萱","若曦","佳怡","可馨",
    "子涵","紫萱","雨萱","美琪","诗琪","晓雯","雅琴","语桐","心怡","雪莹",
]

# 课程→部门映射
COURSE_DEPT_MAP = {
    "语文":   "CHN-DEPT",
    "数学":   "MATH-DEPT",
    "英语":   "ENG-DEPT",
    "物理":   "SCI-DEPT",
    "化学":   "SCI-DEPT",
    "生物":   "SCI-DEPT",
    "科学":   "SCI-DEPT",
    "历史":   "HUM-DEPT",
    "地理":   "HUM-DEPT",
    "道德与法治": "HUM-DEPT",
    "思想政治":   "HUM-DEPT",
    "体育与健康": "PE-ART-DEPT",
    "音乐":   "PE-ART-DEPT",
    "美术":   "PE-ART-DEPT",
    "信息技术":   "TECH-DEPT",
    "通用技术":   "TECH-DEPT",
    "劳动":   "TECH-DEPT",
    "综合实践":   "COMP-DEPT",
    "物理选择性必修": "SCI-DEPT",
    "化学选择性必修": "SCI-DEPT",
    "生物选择性必修": "SCI-DEPT",
    "历史选择性必修": "HUM-DEPT",
    "地理选择性必修": "HUM-DEPT",
}

# 课程→学科（用于教师 profile）
COURSE_SUBJECT_MAP = {
    "语文": "语文", "数学": "数学", "英语": "英语",
    "物理": "物理", "化学": "化学", "生物": "生物", "科学": "科学",
    "历史": "历史", "地理": "地理",
    "道德与法治": "道德与法治", "思想政治": "思想政治",
    "体育与健康": "体育", "音乐": "音乐", "美术": "美术",
    "信息技术": "信息技术", "通用技术": "通用技术",
    "劳动": "劳动", "综合实践": "综合实践",
    "物理选择性必修": "物理", "化学选择性必修": "化学",
    "生物选择性必修": "生物", "历史选择性必修": "历史",
    "地理选择性必修": "地理",
}

# 教师职称
TITLES = ["二级教师", "一级教师", "高级教师", "正高级教师"]
EDUCATIONS = ["本科", "硕士", "博士"]


# ============================================================
# 辅助函数
# ============================================================

def generate_student_no(grade_level: int, class_idx: int, seq: int) -> str:
    """生成学号: STU + 年级(2位) + 班级(2位) + 序号(2位) + 校验"""
    return f"STU{grade_level:02d}{class_idx:02d}{seq:02d}"


def generate_employee_no(dept_code: str, seq: int) -> str:
    """生成工号"""
    return f"T{dept_code[:3]}{seq:03d}"


def random_phone() -> str:
    """随机手机号"""
    prefixes = ["130","131","132","133","134","135","136","137","138","139",
                "150","151","152","153","155","156","157","158","159",
                "180","181","182","183","184","185","186","187","188","189"]
    return random.choice(prefixes) + "".join([str(random.randint(0,9)) for _ in range(8)])


def random_id_card(birth_date: date, gender: str) -> str:
    """生成18位身份证号（地区码用440400=珠海）"""
    area = "440400"                       # 6位
    birth_str = birth_date.strftime("%Y%m%d")  # 8位
    # 生成3位顺序码，确保奇偶性与性别匹配，且不会溢出到4位
    seq = random.randint(100, 998)
    if gender == "male":
        seq = seq if seq % 2 == 1 else seq + 1
    else:
        seq = seq if seq % 2 == 0 else seq - 1  # 用 -1 避免溢出
    body = area + birth_str + f"{seq:03d}"  # 6+8+3=17位，强制3位
    # 校验码
    weights = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2]
    check_chars = "10X98765432"
    total = sum(int(body[i]) * weights[i] for i in range(17))
    check = check_chars[total % 11]
    return body + check


def random_name(gender: str) -> str:
    surname = random.choice(SURNAMES)
    if gender == "male":
        given = random.choice(GIVEN_NAMES_MALE)
    else:
        given = random.choice(GIVEN_NAMES_FEMALE)
    return surname + given


def compute_birth_date(grade_level: int) -> date:
    """
    计算出生日期。小学入学年龄一律6岁。
    2025-2026学年，一年级=6岁 → 2019年出生
    grade_level=1 → birth_year=2025-6=2019
    grade_level=N → birth_year=2025-6-(N-1)=2020-N
    """
    birth_year = 2025 - 6 - (grade_level - 1)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # 简化，避免月份天数问题
    return date(birth_year, month, day)


# ============================================================
# 主逻辑
# ============================================================

async def seed_all():
    """执行全部种子数据生成"""
    async with async_session_factory() as session:
        # ─── 检查是否已有数据 ───
        result = await session.execute(select(func.count(User.id)))
        user_count = result.scalar()
        if user_count > 1:  # 已有 admin
            print(f"⚠️  数据库已有 {user_count} 个用户，跳过种子数据生成。如需重新生成，请先清空数据库。")
            return

        print("=" * 60)
        print("🌱 智慧校园 - 种子数据生成")
        print("=" * 60)

        # ─── 1. 创建部门 ───
        print("\n📁 创建部门...")
        dept_map = {}  # code → Department
        for name, code, desc, level in DEPARTMENTS:
            dept = Department(
                id=uuid4(),
                name=name,
                code=code,
                description=desc,
                level=level,
                status="active",
            )
            session.add(dept)
            dept_map[code] = dept
        await session.flush()
        print(f"   ✅ 创建 {len(dept_map)} 个部门")

        # ─── 2. 创建角色 ───
        print("\n👑 创建角色...")
        role_map = {}
        for code, name, desc, level in ROLES:
            role = Role(
                id=uuid4(),
                code=code,
                name=name,
                description=desc,
                level=level,
                status="active",
            )
            session.add(role)
            role_map[code] = role
        await session.flush()
        print(f"   ✅ 创建 {len(role_map)} 个角色")

        # ─── 3. 创建年级 ───
        print("\n📊 创建年级...")
        grade_map = {}  # grade_level → Grade
        grade_id_by_level = {}
        for name, code, grade_level, phase, edu_year in GRADES:
            grade = Grade(
                id=uuid4(),
                name=name,
                code=code,
                academic_year=ACADEMIC_YEAR,
                year=2025,
                grade_level=grade_level,
                student_count=0,
                class_count=4,
                status="active",
                description=f"{'小学' if phase=='primary' else '初中' if phase=='junior' else '高中'}{name}",
            )
            session.add(grade)
            grade_map[grade_level] = grade
            grade_id_by_level[grade_level] = grade.id
        await session.flush()
        print(f"   ✅ 创建 {len(grade_map)} 个年级")

        # ─── 4. 创建教师 ───
        # 先创建教师，后面班级需要班主任
        print("\n👨‍🏫 创建教师...")

        # 统计每门课需要多少老师
        # 收集所有 (课程名, 学段) 的唯一组合
        course_teacher_needed = {}  # (course_name, phase) → count_needed
        for course_name, prefix, cat, credit, hours, exam_type, phases in COURSES_SPEC:
            for phase in phases:
                key = (course_name, phase)
                if key not in course_teacher_needed:
                    course_teacher_needed[key] = 0
                course_teacher_needed[key] += 1  # 该学段有几个年级就需要覆盖

        # 每个唯一学科至少2个老师
        # 先按学科去重
        subject_teachers_needed = {}  # subject → min_teachers
        for (course_name, phase), count in course_teacher_needed.items():
            subject = COURSE_SUBJECT_MAP.get(course_name, course_name)
            # 该学科在该学段有 count 个年级，至少2个老师覆盖
            needed = max(2, (count + 1) // 2)  # 确保至少2个
            if subject not in subject_teachers_needed:
                subject_teachers_needed[subject] = 0
            subject_teachers_needed[subject] = max(subject_teachers_needed[subject], needed)

        # 高中选修课也需要额外老师
        for subject, needed in list(subject_teachers_needed.items()):
            subject_teachers_needed[subject] = max(needed, 2)

        # 实际分配教师人数：每个学科3-5名老师
        teacher_users = []  # list of User
        teacher_profiles = []  # list of TeacherProfile
        teacher_by_subject = {}  # subject → [User, ...]

        teacher_idx = 0
        for subject in sorted(subject_teachers_needed.keys()):
            count = random.randint(3, 5)  # 每学科3-5名
            dept_code = COURSE_DEPT_MAP.get(subject, "ACAD")
            dept = dept_map.get(dept_code)

            for i in range(count):
                teacher_idx += 1
                gender = random.choice(["male", "female"])
                name = random_name(gender)
                username = f"teacher_{subject}_{i+1}"

                # 教师25-55岁
                age = random.randint(25, 55)
                birth_year = 2025 - age
                birth = date(birth_year, random.randint(1,12), random.randint(1,28))

                user = User(
                    id=uuid4(),
                    username=username,
                    email=f"{username}@smartcampus.edu",
                    phone=random_phone(),
                    password_hash=get_password_hash(DEFAULT_PASSWORD),
                    real_name=name,
                    department_id=dept.id if dept else None,
                    position="教师",
                    gender=gender,
                    birth_date=datetime(birth.year, birth.month, birth.day),
                    status="active",
                )
                session.add(user)
                teacher_users.append(user)

                profile = TeacherProfile(
                    id=uuid4(),
                    user_id=user.id,
                    employee_no=generate_employee_no(dept_code, teacher_idx),
                    hire_date=datetime(birth_year + 22, 9, 1),  # 假设22岁入职
                    position="教师",
                    title=random.choice(TITLES),
                    employment_type="full_time",
                    subject=subject,
                    teaching_grade="全学段",
                    education=random.choice(EDUCATIONS),
                )
                session.add(profile)
                teacher_profiles.append(profile)

                if subject not in teacher_by_subject:
                    teacher_by_subject[subject] = []
                teacher_by_subject[subject].append(user)

        await session.flush()
        print(f"   ✅ 创建 {len(teacher_users)} 名教师（覆盖 {len(teacher_by_subject)} 个学科）")

        # ─── 5. 创建班级 + 学生 ───
        print("\n🏫 创建班级和学生...")
        total_students = 0
        all_classes = []
        head_teacher_pool = list(teacher_users)  # 班主任池

        for grade_level, grade in grade_map.items():
            for class_idx, suffix in enumerate(CLASS_SUFFIXES, 1):
                class_name = f"{grade.name}{suffix}"
                class_code = f"{grade.code}-C{class_idx:02d}"

                # 随机选一个班主任
                head_teacher = random.choice(head_teacher_pool)

                cls = Class(
                    id=uuid4(),
                    name=class_name,
                    code=class_code,
                    grade_id=grade.id,
                    head_teacher_id=head_teacher.id,
                    student_count=30,
                    room_no=f"{grade_level}{class_idx:02d}",
                    academic_year=ACADEMIC_YEAR,
                    semester=SEMESTER,
                    status="active",
                )
                session.add(cls)
                all_classes.append(cls)

                # 创建30个学生
                for seq in range(1, 31):
                    gender = random.choice(["male", "female"])
                    name = random_name(gender)
                    birth_date = compute_birth_date(grade_level)
                    enrollment_year = 2025 - (grade_level - 1) if grade_level <= 6 else \
                                     2025 - (grade_level - 7) if grade_level <= 9 else \
                                     2025 - (grade_level - 10)

                    student = Student(
                        id=uuid4(),
                        student_no=generate_student_no(grade_level, class_idx, seq),
                        name=name,
                        gender=gender,
                        birth_date=datetime(birth_date.year, birth_date.month, birth_date.day),
                        id_card=random_id_card(birth_date, gender),
                        nation=random.choice(["汉族","汉族","汉族","汉族","回族","壮族","满族","苗族","土家族"]),
                        address=f"珠海市香洲区{random.choice(['翠香','梅华','前山','拱北','吉大','南屏'])}街道某某小区",
                        phone=random_phone() if random.random() > 0.7 else None,
                        guardian_name=random_name("female" if random.random() > 0.5 else "male"),
                        guardian_phone=random_phone(),
                        enrollment_date=datetime(enrollment_year, 9, 1),
                        grade_id=grade.id,
                        class_id=cls.id,
                        status="active",
                    )
                    session.add(student)
                    total_students += 1

        await session.flush()
        print(f"   ✅ 创建 {len(all_classes)} 个班级")
        print(f"   ✅ 创建 {total_students} 名学生")

        # ─── 6. 创建课程 ───
        print("\n📚 创建课程...")
        total_courses = 0
        course_records = []

        for course_name, prefix, cat, credit, hours, exam_type, phases in COURSES_SPEC:
            for phase in phases:
                # 该学段对应的年级列表
                if phase == "primary":
                    grade_levels = [1,2,3,4,5,6]
                elif phase == "junior":
                    grade_levels = [7,8,9]
                else:
                    grade_levels = [10,11,12]

                for gl in grade_levels:
                    grade = grade_map[gl]
                    grade_code = grade.code

                    # 为课程分配老师（至少2位）
                    subject = COURSE_SUBJECT_MAP.get(course_name, course_name)
                    available_teachers = teacher_by_subject.get(subject, teacher_users)
                    # 选2-3位老师，第一人为主讲
                    n_teachers = min(len(available_teachers), random.randint(2, 3))
                    chosen = random.sample(available_teachers, n_teachers)
                    primary_teacher = chosen[0]

                    # 课程编码: 前缀-年级-序号
                    course_code = f"{prefix}-{grade_code}"
                    # 同一学科同年级可能有多个（如高中选修），加序号
                    seq_suffix = ""
                    if "选择性必修" in course_name:
                        seq_suffix = "-S"

                    course = Course(
                        id=uuid4(),
                        code=f"{course_code}{seq_suffix}",
                        name=course_name,
                        category=cat,
                        credit=credit if credit > 0 else None,
                        hours=hours,
                        teacher_id=primary_teacher.id,
                        grade_id=grade.id,
                        semester=SEMESTER,
                        exam_type=exam_type,
                        status="active",
                    )
                    session.add(course)
                    course_records.append(course)
                    total_courses += 1

        await session.flush()
        print(f"   ✅ 创建 {total_courses} 门课程实例")

        # ─── 7. 更新年级统计 ───
        print("\n📈 更新年级统计...")
        for grade_level, grade in grade_map.items():
            grade.student_count = 30 * 4  # 每年级4班×30人
            grade.class_count = 4

        await session.flush()

        # ─── 提交 ───
        await session.commit()

        # ─── 输出统计 ───
        print("\n" + "=" * 60)
        print("✅ 种子数据生成完毕！")
        print("=" * 60)
        print(f"  📁 部门:       {len(dept_map)}")
        print(f"  👑 角色:       {len(role_map)}")
        print(f"  📊 年级:       {len(grade_map)}")
        print(f"  👨‍🏫 教师:       {len(teacher_users)}")
        print(f"  🏫 班级:       {len(all_classes)}")
        print(f"  👨‍🎓 学生:       {total_students}")
        print(f"  📚 课程实例:   {total_courses}")
        print(f"\n  🔑 教师默认密码: {DEFAULT_PASSWORD}")
        print(f"  🔑 管理员账号:   admin / admin123")
        print("=" * 60)


async def main():
    """入口"""
    try:
        await seed_all()
    except Exception as e:
        print(f"\n❌ 种子数据生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
