"""
生成测试数据脚本
用法: python generate_test_data.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from uuid import uuid4
import random
import bcrypt

from sqlalchemy import text
from app.core.database import async_session_factory, engine, Base


GRADES = [
    {"name": "一年级", "code": "G01", "grade_level": 1},
    {"name": "二年级", "code": "G02", "grade_level": 2},
    {"name": "三年级", "code": "G03", "grade_level": 3},
    {"name": "四年级", "code": "G04", "grade_level": 4},
    {"name": "五年级", "code": "G05", "grade_level": 5},
    {"name": "六年级", "code": "G06", "grade_level": 6},
    {"name": "七年级", "code": "G07", "grade_level": 7},
    {"name": "八年级", "code": "G08", "grade_level": 8},
    {"name": "九年级", "code": "G09", "grade_level": 9},
    {"name": "高一年级", "code": "G10", "grade_level": 10},
    {"name": "高二年级", "code": "G11", "grade_level": 11},
    {"name": "高三年级", "code": "G12", "grade_level": 12},
]

SUBJECTS = [
    {"code": "CN", "name": "语文", "category": "language"},
    {"code": "MA", "name": "数学", "category": "science"},
    {"code": "EN", "name": "英语", "category": "language"},
    {"code": "PE", "name": "体育", "category": "physical"},
    {"code": "AR", "name": "美术", "category": "art"},
    {"code": "MU", "name": "音乐", "category": "art"},
    {"code": "ME", "name": "道德与法治", "category": "social"},
    {"code": "SC", "name": "科学", "category": "science"},
    {"code": "PH", "name": "物理", "category": "science"},
    {"code": "CH", "name": "化学", "category": "science"},
    {"code": "HI", "name": "历史", "category": "social"},
    {"code": "GE", "name": "地理", "category": "social"},
    {"code": "BI", "name": "生物", "category": "science"},
    {"code": "PO", "name": "政治", "category": "social"},
]

COURSE_TOPICS = {
    "MA": [
        {"code": "MA_GEO", "name": "几何"},
        {"code": "MA_ALG", "name": "代数"},
        {"code": "MA_CAL", "name": "微积分"},
        {"code": "MA_STA", "name": "概率统计"},
    ],
    "CN": [
        {"code": "CN_REA", "name": "阅读理解"},
        {"code": "CN_WRI", "name": "写作"},
        {"code": "CN_CLAS", "name": "文言文"},
    ],
    "EN": [
        {"code": "EN_GRA", "name": "语法"},
        {"code": "EN_REA", "name": "阅读"},
        {"code": "EN_WRI", "name": "写作"},
        {"code": "EN_SPE", "name": "口语"},
    ],
    "HI": [
        {"code": "HI_AN", "name": "中国古代史"},
        {"code": "HI_MOD", "name": "近现代史"},
        {"code": "HI_WOR", "name": "世界历史"},
    ],
    "GE": [
        {"code": "GE_CHI", "name": "中国地理"},
        {"code": "GE_WOR", "name": "世界地理"},
        {"code": "GE_MAP", "name": "地图学"},
    ],
    "PH": [
        {"code": "PH_MEC", "name": "力学"},
        {"code": "PH_ELE", "name": "电磁学"},
        {"code": "PH_OPT", "name": "光学"},
        {"code": "PH_MOD", "name": "现代物理"},
    ],
    "CH": [
        {"code": "CH_INO", "name": "无机化学"},
        {"code": "CH_ORG", "name": "有机化学"},
        {"code": "CH_ANL", "name": "分析化学"},
    ],
    "BI": [
        {"code": "BI_BOT", "name": "植物学"},
        {"code": "BI_ZOO", "name": "动物学"},
        {"code": "BI_MOL", "name": "分子生物学"},
    ],
}

GENDER = ["male", "female"]
NATIONS = ["汉族", "回族", "满族", "维吾尔族", "苗族", "彝族", "壮族", "藏族"]


def init_db():
    import sqlite3

    conn = sqlite3.connect("smart_campus.db")
    cursor = conn.cursor()

    tables = ["departments", "users", "grades", "classes", "courses", "students"]

    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except:
            pass

    conn.commit()

    admin_id = str(uuid4())
    pw_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO users (id, username, password_hash, real_name, position, gender, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            admin_id,
            "admin",
            pw_hash,
            "管理员",
            "系统管理员",
            "male",
            "active",
            datetime.now(),
            datetime.now(),
        ),
    )
    cursor.execute(
        "INSERT INTO departments (id, name, code, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid4()), "管理员", "ADMIN", "active", datetime.now(), datetime.now()),
    )

    conn.commit()
    conn.close()
    print("Database cleared, admin user created.")


async def create_department(session, name: str) -> str:
    dept_id = str(uuid4())
    await session.execute(
        text("""INSERT INTO departments (id, name, code, status, created_at, updated_at)
                VALUES (:id, :name, :code, 'active', :now, :now)"""),
        {"id": dept_id, "name": name, "code": name[:2].upper(), "now": datetime.now()},
    )
    return dept_id


async def create_user(
    session,
    username: str,
    real_name: str,
    password: str,
    department_id: str,
    position: str,
    gender: str,
) -> str:
    user_id = str(uuid4())
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    await session.execute(
        text("""INSERT INTO users (id, username, password_hash, real_name, department_id, 
                position, gender, status, created_at, updated_at)
                VALUES (:id, :username, :pw_hash, :real_name, :dept_id, 
                :position, :gender, 'active', :now, :now)"""),
        {
            "id": user_id,
            "username": username,
            "pw_hash": pw_hash,
            "real_name": real_name,
            "dept_id": department_id,
            "position": position,
            "gender": gender,
            "now": datetime.now(),
        },
    )
    return user_id


async def create_grades(session, academic_year: str):
    grade_ids = []
    for grade in GRADES:
        grade_id = str(uuid4())
        await session.execute(
            text("""INSERT INTO grades (id, name, code, academic_year, grade_level, 
                    student_count, class_count, status, created_at, updated_at)
                    VALUES (:id, :name, :code, :academic_year, :level, 0, 0, 'active', :now, :now)"""),
            {
                "id": grade_id,
                "name": grade["name"],
                "code": grade["code"],
                "academic_year": academic_year,
                "level": grade["grade_level"],
                "now": datetime.now(),
            },
        )
        grade_ids.append(grade_id)
    return grade_ids


async def create_classes(session, grade_ids: list, academic_year: str):
    class_ids = []
    for grade_idx, grade_id in enumerate(grade_ids):
        for class_num in range(1, 3):
            class_id = str(uuid4())
            class_code = f"{GRADES[grade_idx]['code']}-{class_num}"
            await session.execute(
                text("""INSERT INTO classes (id, name, code, grade_id, student_count, 
                        academic_year, semester, status, created_at, updated_at)
                        VALUES (:id, :name, :code, :grade_id, 0, :year, '1', 'active', :now, :now)"""),
                {
                    "id": class_id,
                    "name": f"{GRADES[grade_idx]['name']}{class_num}班",
                    "code": class_code,
                    "grade_id": grade_id,
                    "year": academic_year,
                    "now": datetime.now(),
                },
            )
            class_ids.append(class_id)
    return class_ids


async def create_teachers(session, department_id: str, count: int = 50) -> list:
    teachers = []
    surnames = [
        "张",
        "李",
        "王",
        "刘",
        "陈",
        "杨",
        "赵",
        "黄",
        "周",
        "吴",
        "徐",
        "孙",
        "胡",
        "朱",
        "高",
        "林",
        "何",
        "郭",
        "马",
        "罗",
    ]
    given_names = [
        "伟",
        "芳",
        "娜",
        "敏",
        "静",
        "丽",
        "强",
        "磊",
        "军",
        "洋",
        "勇",
        "艳",
        "杰",
        "涛",
        "明",
        "超",
        "秀英",
        "华",
        "鑫",
        "宇",
    ]

    positions = [
        "语文教师",
        "数学教师",
        "英语教师",
        "物理教师",
        "化学教师",
        "历史教师",
        "地理教师",
        "生物教师",
        "政治教师",
        "体育教师",
        "美术教师",
        "音乐教师",
        "科学教师",
        "班主任",
    ]

    for i in range(count):
        surname = random.choice(surnames)
        given = random.choice(given_names)
        name = surname + given
        username = f"teacher_{i + 1:03d}"

        user_id = await create_user(
            session,
            username,
            name,
            "teacher123",
            department_id,
            random.choice(positions),
            random.choice(GENDER),
        )
        teachers.append(user_id)
    return teachers


async def create_courses(session, grade_ids: list, teachers: list):
    course_ids = []

    for grade_idx, grade_id in enumerate(grade_ids):
        grade_level = GRADES[grade_idx]["grade_level"]

        if grade_level <= 6:
            relevant_subjects = [
                s
                for s in SUBJECTS
                if s["code"] in ["CN", "MA", "EN", "PE", "AR", "MU", "ME", "SC"]
            ]
        elif grade_level <= 9:
            relevant_subjects = [
                s
                for s in SUBJECTS
                if s["code"]
                in [
                    "CN",
                    "MA",
                    "EN",
                    "PE",
                    "AR",
                    "MU",
                    "ME",
                    "PH",
                    "CH",
                    "BI",
                    "HI",
                    "GE",
                ]
            ]
        else:
            relevant_subjects = SUBJECTS

        for subject in relevant_subjects:
            course_id = str(uuid4())
            teacher_id = random.choice(teachers) if teachers else None

            await session.execute(
                text("""INSERT INTO courses (id, code, name, category, credit, hours, teacher_id, 
                        grade_id, semester, status, created_at, updated_at)
                        VALUES (:id, :code, :name, :category, 4, 72, :teacher_id, 
                        :grade_id, '1', 'active', :now, :now)"""),
                {
                    "id": course_id,
                    "code": f"{subject['code']}_{GRADES[grade_idx]['code']}",
                    "name": subject["name"],
                    "category": subject["category"],
                    "teacher_id": teacher_id,
                    "grade_id": grade_id,
                    "now": datetime.now(),
                },
            )
            course_ids.append(course_id)

            if subject["code"] in COURSE_TOPICS:
                for topic in COURSE_TOPICS[subject["code"]]:
                    topic_id = str(uuid4())
                    topic_code = f"{topic['code']}_{GRADES[grade_idx]['code']}"
                    await session.execute(
                        text("""INSERT INTO courses (id, code, name, category, credit, hours, 
                                teacher_id, grade_id, semester, status, created_at, updated_at)
                                VALUES (:id, :code, :name, :category, 2, 36, :teacher_id, 
                                :grade_id, '1', 'active', :now, :now)"""),
                        {
                            "id": topic_id,
                            "code": topic_code,
                            "name": topic["name"],
                            "category": subject["category"],
                            "teacher_id": teacher_id,
                            "grade_id": grade_id,
                            "now": datetime.now(),
                        },
                    )
                    course_ids.append(topic_id)

    return course_ids


async def create_students(session, class_ids: list, grade_ids: list):
    student_count = 0

    surnames = [
        "张",
        "李",
        "王",
        "刘",
        "陈",
        "杨",
        "赵",
        "黄",
        "周",
        "吴",
        "徐",
        "孙",
        "胡",
        "朱",
        "高",
        "林",
        "何",
        "郭",
        "马",
        "罗",
        "宋",
        "谢",
        "韩",
        "唐",
        "冯",
        "于",
        "董",
        "萧",
        "程",
        "曹",
    ]
    given_names = [
        "伟",
        "芳",
        "娜",
        "敏",
        "静",
        "丽",
        "强",
        "磊",
        "军",
        "洋",
        "勇",
        "艳",
        "杰",
        "涛",
        "明",
        "超",
        "秀英",
        "华",
        "鑫",
        "宇",
        "浩然",
        "子涵",
        "思雨",
        "欣怡",
        "博文",
        "一诺",
        "欣悦",
        "子轩",
    ]

    for class_idx, class_id in enumerate(class_ids):
        grade_idx = class_idx // 2
        grade_id = grade_ids[grade_idx]

        for i in range(30):
            student_id = str(uuid4())
            surname = random.choice(surnames)
            given = random.choice(given_names)
            name = surname + given
            student_no = f"2024{grade_idx + 1:02d}{class_idx % 2 + 1:01d}{i + 1:03d}"
            gender = random.choice(GENDER)
            nation = random.choice(NATIONS)
            birth_year = 2024 - (GRADES[grade_idx]["grade_level"] + 5)

            await session.execute(
                text("""INSERT INTO students (id, student_no, name, gender, birth_date, nation, 
                        grade_id, class_id, status, enrollment_date, created_at, updated_at)
                        VALUES (:id, :no, :name, :gender, :birth, :nation, 
                        :grade_id, :class_id, 'active', :enroll, :now, :now)"""),
                {
                    "id": student_id,
                    "no": student_no,
                    "name": name,
                    "gender": gender,
                    "birth": datetime(
                        birth_year, random.randint(1, 12), random.randint(1, 28)
                    ),
                    "nation": nation,
                    "grade_id": grade_id,
                    "class_id": class_id,
                    "enroll": datetime(2024, 9, 1),
                    "now": datetime.now(),
                },
            )
            student_count += 1

    return student_count


async def main():
    print("Initializing database...")
    init_db()

    async with async_session_factory() as session:
        try:
            print("Creating departments...")
            dept_id = await create_department(session, "教务处")

            print("Creating teachers...")
            teachers = await create_teachers(session, dept_id, 50)
            await session.commit()
            print(f"Created {len(teachers)} teachers")

            print("Creating academic year 2024-2025...")
            academic_year = "2024-2025"

            print("Creating grades...")
            grade_ids = await create_grades(session, academic_year)
            await session.commit()
            print(f"Created {len(grade_ids)} grades")

            print("Creating classes...")
            class_ids = await create_classes(session, grade_ids, academic_year)
            await session.commit()
            print(f"Created {len(class_ids)} classes")

            print("Creating courses...")
            course_ids = await create_courses(session, grade_ids, teachers)
            await session.commit()
            print(f"Created {len(course_ids)} courses")

            print("Creating students...")
            student_count = await create_students(session, class_ids, grade_ids)
            await session.commit()
            print(f"Created {student_count} students")

            print("\n=== Test Data Summary ===")
            print(f"Grades: {len(GRADES)} (小一 to 高三)")
            print(f"Classes: {len(class_ids)} (2 per grade)")
            print(f"Students: {student_count} (30 per class)")
            print(f"Teachers: {len(teachers)}")
            print(f"Courses: {len(course_ids)} (subjects + topics)")
            print("\nTest data generation completed!")

        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(main())
