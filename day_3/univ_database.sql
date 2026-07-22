CREATE TABLE majors (
    major_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    major_name VARCHAR(100) NOT NULL UNIQUE,
    major_code VARCHAR(20) NOT NULL UNIQUE,
    major_created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE students (
    student_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    major_id BIGINT NOT NULL REFERENCES majors (major_id),
    student_email VARCHAR(200) NOT NULL UNIQUE,
    student_pw VARCHAR(200) NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    student_grade SMALLINT NOT NULL DEFAULT 1 CHECK (student_grade BETWEEN 1 AND 4),
    student_created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE courses (
    course_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    major_id BIGINT NOT NULL REFERENCES majors (major_id),
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_credits SMALLINT NOT NULL CHECK (
        course_credits BETWEEN 1 AND 6
    ),
    course_created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE enrollments (
    student_id BIGINT NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses (course_id) ON DELETE CASCADE,
    course_score SMALLINT CHECK (
        course_score BETWEEN 0 AND 100
    ),
    course_status VARCHAR(20) NOT NULL DEFAULT 'ENROLLED' CHECK (
        course_status IN (
            'ENROLLED',
            'COMPLETED',
            'CANCELLED'
        )
    ),
    enrollment_created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (student_id, course_id)
);

-----------------------
---------insert -------
-----------------------

INSERT INTO
    majors (major_name, major_code)
VALUES ('컴퓨터공학과', 'CS'),
    ('인공지능학과', 'AI'),
    ('경영학과', 'BA'),
    ('전자공학과', 'EE') ON CONFLICT DO NOTHING;

INSERT INTO
    students (
        major_id,
        student_email,
        student_pw,
        student_name,
        student_grade,
        student_phone
    )
VALUES (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        'minjun@example.com',
        'hashed_pw_01',
        '김민준',
        1,
        '010-1000-1001'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        'seoyeon@example.com',
        'hashed_pw_02',
        '이서연',
        2,
        '010-1000-1002'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        'jihoon@example.com',
        'hashed_pw_03',
        '박지훈',
        3,
        '010-1000-1003'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'AI'
        ),
        'hayoon@example.com',
        'hashed_pw_04',
        '최하윤',
        1,
        '010-1000-1004'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'AI'
        ),
        'doyoon@example.com',
        'hashed_pw_05',
        '정도윤',
        2,
        '010-1000-1005'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'AI'
        ),
        'yujin@example.com',
        'hashed_pw_06',
        '한유진',
        4,
        '010-1000-1006'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'BA'
        ),
        'junseo@example.com',
        'hashed_pw_07',
        '강준서',
        1,
        '010-1000-1007'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'BA'
        ),
        'sua@example.com',
        'hashed_pw_08',
        '윤수아',
        3,
        '010-1000-1008'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'EE'
        ),
        'hyunwoo@example.com',
        'hashed_pw_09',
        '장현우',
        2,
        '010-1000-1009'
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'EE'
        ),
        'jieun@example.com',
        'hashed_pw_10',
        '임지은',
        4,
        '010-1000-1010'
    ) ON CONFLICT DO NOTHING;

INSERT INTO
    courses (
        major_id,
        course_name,
        course_code,
        course_credits
    )
VALUES (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        '데이터베이스',
        'CS101',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        '알고리즘',
        'CS102',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        '운영체제',
        'CS103',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'CS'
        ),
        '컴퓨터네트워크',
        'CS104',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'AI'
        ),
        '머신러닝기초',
        'AI101',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'AI'
        ),
        '딥러닝입문',
        'AI102',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'BA'
        ),
        '경영학원론',
        'BA101',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'BA'
        ),
        '마케팅원론',
        'BA102',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'EE'
        ),
        '회로이론',
        'EE101',
        3
    ),
    (
        (
            SELECT major_id
            FROM majors
            WHERE
                major_code = 'EE'
        ),
        '디지털논리회로',
        'EE102',
        3
    ) ON CONFLICT DO NOTHING;

INSERT INTO
    enrollments (
        student_id,
        course_id,
        course_score,
        course_status
    )
VALUES (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'minjun@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS101'
        ),
        95,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'minjun@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS102'
        ),
        NULL,
        'ENROLLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'seoyeon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS101'
        ),
        88,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'seoyeon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS103'
        ),
        NULL,
        'ENROLLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'jihoon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS104'
        ),
        91,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'hayoon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'AI101'
        ),
        NULL,
        'ENROLLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'hayoon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'AI102'
        ),
        93,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'doyoon@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'AI101'
        ),
        84,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'yujin@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'AI102'
        ),
        NULL,
        'CANCELLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'junseo@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'BA101'
        ),
        NULL,
        'ENROLLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'sua@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'BA102'
        ),
        87,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'hyunwoo@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'EE101'
        ),
        79,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'hyunwoo@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'EE102'
        ),
        NULL,
        'ENROLLED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'jieun@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'EE101'
        ),
        90,
        'COMPLETED'
    ),
    (
        (
            SELECT student_id
            FROM students
            WHERE
                student_email = 'jieun@example.com'
        ),
        (
            SELECT course_id
            FROM courses
            WHERE
                course_code = 'CS101'
        ),
        NULL,
        'ENROLLED'
    ) ON CONFLICT DO NOTHING;

SELECT
    student_id,
    student_name,
    student_email,
    student_grade,
    student_phone
FROM univ.students
WHERE
    student_grade BETWEEN 1 AND 3
ORDER BY student_grade ASC, student_name ASC;

SELECT
    student_id,
    course_id,
    COALESCE(course_score, 0) AS score_display,
    CASE course_status
        WHEN 'ENROLLED' THEN '수강 중'
        WHEN 'COMPLETED' THEN '수강 완료'
        WHEN 'CANCELLED' THEN '수강 취소'
        ELSE '상태 미확인'
    END AS status_display,
    TO_CHAR (
        enrollment_created_at,
        'YYYY-MM-DD HH24:MI'
    ) AS created_date
FROM univ.enrollments
ORDER BY student_id, course_id;

SELECT
    s.student_name AS student_name,
    m.major_name AS major_name,
    c.course_code AS course_code,
    c.course_name AS course_name,
    e.course_score AS course_score,
    e.course_status AS course_status
FROM univ.enrollments e
    JOIN univ.students s ON s.student_id = e.student_id
    JOIN univ.majors m ON m.major_id = s.major_id
    JOIN univ.courses c ON c.course_id = e.course_id
ORDER BY s.student_name, c.course_code;