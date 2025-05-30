-- 1. Define tables with corrected data types, checks, and constraints
CREATE TABLE UserLogin (
  role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'professor', 'admin')),
  userId INT PRIMARY KEY,
  password VARCHAR(255) NOT NULL
);

CREATE TABLE Degree (
  degreeId int PRIMARY KEY,
  degreeName varchar(100) NOT NULL,
  ugPgType varchar(2) NOT NULL CHECK (ugPgType IN ('UG', 'PG')),
  maxYears int NOT NULL CHECK (maxYears > 0),
  totalCreditsRequired int NOT NULL CHECK (totalCreditsRequired > 0),
  coreCreditsRequired int NOT NULL CHECK (coreCreditsRequired <= totalCreditsRequired)
);

-- Department: Allow headOfDeptId to be nullable initially
CREATE TABLE Department (
  departmentId int PRIMARY KEY,
  deptName varchar(100) NOT NULL,
  headOfDeptId int -- Temporarily nullable to resolve circular dependency
);

CREATE TABLE Professors (
  professorId int PRIMARY KEY,
  departmentId int NOT NULL, 
  professorName varchar(100) NOT NULL,
  dob date NOT NULL,
  gender varchar(10) CHECK (gender IN ('Male', 'Female', 'Other')),
  WorkingStatus varchar(10) CHECK (WorkingStatus IN ('Active', 'Departed'))
);

-- Students: Standardize column names (deptId → departmentId)
CREATE TABLE Students (
  studentId int PRIMARY KEY,
  studentName varchar(100) NOT NULL,
  degreeId int NOT NULL,
  departmentId int NOT NULL, -- Renamed from deptId
  dateOfJoining  date NOT NULL,
  gender varchar(10) CHECK (gender IN ('Male', 'Female', 'Other')),
  dob date NOT NULL,
  dateOfGraduation date CHECK (dateOfGraduation>dateOfJoining),
  graduationStatus varchar(20) NOT NULL CHECK(graduationStatus in ('Graduated','In Progress','Discontinued', 'Max years exceeded'))
);

CREATE TABLE Courses (
  courseId int PRIMARY KEY,
  courseName varchar(100) NOT NULL,
  departmentId int NOT NULL, -- Renamed from deptId
  typeOfCourse varchar(2) NOT NULL CHECK (typeOfCourse IN ('UG', 'PG')),
  courseType varchar(20) CHECK (courseType IN ('Theory', 'Lab')), -- Renamed from 'type'
  credits int NOT NULL CHECK (credits > 0 AND credits <= 5)
);

CREATE TABLE AcademicTerm (
  termId int PRIMARY KEY,
  termName varchar(50) NOT NULL,
  startDate date NOT NULL,
  endDate date NOT NULL,
  CHECK (endDate > startDate)
);

CREATE TABLE CourseOffering (
  offeringId int PRIMARY KEY,
  courseId int NOT NULL,
  termId int NOT NULL,
  professorId int NOT NULL,
  maxCapacity int NOT NULL CHECK (maxCapacity > 0)
);

CREATE TABLE Enrollment (
  enrollmentId int PRIMARY KEY,
  studentId int NOT NULL,
  offeringId int NOT NULL,
  enrollmentDate date NOT NULL,
  status varchar(20) CHECK (status IN ('Approved', 'Rejected', 'Pending', 'Dropped')),
  UNIQUE (studentId, offeringId) -- Prevent duplicate enrollments
);

CREATE TABLE StudentGrades (
  enrollmentId int PRIMARY KEY,
  grade decimal(5,2) NOT NULL CHECK (grade BETWEEN 0 AND 100),
  remarks text
);

-- 2. Add foreign keys after tables are created
ALTER TABLE Department ADD FOREIGN KEY (headOfDeptId) REFERENCES Professors(professorId) ON DELETE SET NULL;
ALTER TABLE Professors ADD FOREIGN KEY (departmentId) REFERENCES Department(departmentId);
ALTER TABLE Students ADD FOREIGN KEY (degreeId) REFERENCES Degree(degreeId);
ALTER TABLE Students ADD FOREIGN KEY (departmentId) REFERENCES Department(departmentId);
ALTER TABLE Courses ADD FOREIGN KEY (departmentId) REFERENCES Department(departmentId);
ALTER TABLE CourseOffering ADD FOREIGN KEY (courseId) REFERENCES Courses(courseId);
ALTER TABLE CourseOffering ADD FOREIGN KEY (termId) REFERENCES AcademicTerm(termId);
ALTER TABLE CourseOffering ADD FOREIGN KEY (professorId) REFERENCES Professors(professorId);
ALTER TABLE Enrollment ADD FOREIGN KEY (studentId) REFERENCES Students(studentId);
ALTER TABLE Enrollment ADD FOREIGN KEY (offeringId) REFERENCES CourseOffering(offeringId);
ALTER TABLE StudentGrades ADD FOREIGN KEY (enrollmentId) REFERENCES Enrollment(enrollmentId);


INSERT INTO Degree (degreeId, degreeName, ugPgType, maxYears, totalCreditsRequired, coreCreditsRequired)
VALUES 
  (1, 'B.Tech', 'UG', 4, 160, 100),
  (2, 'M.Tech', 'PG', 2, 60, 40);

-- 2. Insert Departments (Branches)
-- headOfDeptId is temporarily set to NULL; we update after inserting professors.
INSERT INTO Department (departmentId, deptName, headOfDeptId)
VALUES 
  (1, 'Computer Science Engineering', NULL),
  (2, 'Data Science Engineering', NULL),
  (3, 'Electrical Engineering', NULL);

-- 3. Insert Professors (one per department)
INSERT INTO Professors (professorId, departmentId, professorName, dob, gender, WorkingStatus)
VALUES 
  (10001, 1, 'Dr. Alice', '1975-06-15', 'Female', 'Active'),
  (10002, 2, 'Dr. Bob', '1980-09-20', 'Male', 'Active'),
  (10003, 3, 'Dr. Carol', '1978-04-10', 'Female', 'Active');

-- 4. Update Departments to assign headOfDeptId from the corresponding professor
UPDATE Department SET headOfDeptId = 10001 WHERE departmentId = 1;
UPDATE Department SET headOfDeptId = 10002 WHERE departmentId = 2;
UPDATE Department SET headOfDeptId = 10003 WHERE departmentId = 3;

-- 5. Insert Students
INSERT INTO Students (studentId, studentName, degreeId, departmentId, dateOfJoining, gender, dob, dateOfGraduation, graduationStatus)
VALUES 
  -- Department 1: Computer Science Engineering (all B.Tech)
  (2000001, 'John Doe', 1, 1, '2023-08-15', 'Male', '2005-05-12', NULL, 'In Progress'),
  (2000002, 'Jane Smith', 1, 1, '2023-08-15', 'Female', '2005-11-30', NULL, 'In Progress'),

  -- Department 2: Data Science Engineering (mix of B.Tech and M.Tech)
  (2000003, 'Mike Brown', 1, 2, '2023-08-15', 'Male', '2005-03-22', NULL, 'In Progress'),
  (2000004, 'Emily White', 2, 2, '2024-01-10', 'Female', '2002-12-05', NULL, 'In Progress'),

  -- Department 3: Electrical Engineering (all B.Tech)
  (2000005, 'Robert Green', 1, 3, '2023-08-15', 'Male', '2005-07-07', NULL, 'In Progress'),
  (2000006, 'Linda Blue', 1, 3, '2023-08-15', 'Female', '2005-09-15', NULL, 'In Progress');

-- 6. Insert Courses
-- Department 1 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, courseType, credits)
VALUES
  (3000001, 'Introduction to Programming', 1, 'UG', 'Theory', 4),
  (3000002, 'Data Structures', 1, 'UG', 'Theory', 4),
  (3000003, 'Programming Lab', 1, 'UG', 'Lab', 2),
  (3000010, 'Natural Language Processing', 2, 'UG', 'Theory', 3),
  (3000011, 'Introduction to AI', 2, 'UG', 'Lab', 5);

-- Department 2 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, courseType, credits)
VALUES
  (3000004, 'Statistics for Data Science', 2, 'UG',  'Theory', 3),
  (3000005, 'Machine Learning Basics', 2, 'UG',  'Theory', 4),
  (3000006, 'Data Science Lab', 2, 'UG', 'Lab', 2);

-- Department 3 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, courseType, credits)
VALUES
  (3000007, 'Circuits and Electronics', 3, 'UG',  'Theory', 4),
  (3000008, 'Electrical Machines', 3, 'UG',  'Theory', 4),
  (3000009, 'Electronics Lab', 3, 'UG', 'Lab', 2);

-- 7. Insert Academic Terms
-- Ongoing term (Spring 2025: current date 2025-04-11 falls between start and end dates)
INSERT INTO AcademicTerm (termId, termName, startDate, endDate)
VALUES 
  (2, 'Spring 2025', '2025-01-10', '2025-05-20');

-- An additional past term to support a completed enrollment and grade (Fall 2024)
INSERT INTO AcademicTerm (termId, termName, startDate, endDate)
VALUES 
  (1, 'Fall 2024', '2024-09-01', '2024-12-15');

-- 8. Insert Course Offerings
-- Ongoing semester offerings (termId = 2)
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  -- For Department 1
  (4000002, 3000001, 2, 10001, 30),
  (4000003, 3000002, 2, 10001, 30),
  -- For Department 2
  (4000004, 3000004, 2, 10002, 25),
  (4000005, 3000005, 2, 10002, 25),
  -- For Department 3
  (4000006, 3000007, 2, 10003, 20),
  (4000007, 3000008, 2, 10003, 20),
  (4000008, 3000003, 2, 10001, 25),
  (4000009, 3000010, 2, 10002, 30),
  (4000010, 3000011, 2, 10002, 40);

-- Past term offering (termId = 1) to demonstrate StudentGrades entry.
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  (4000000, 3000005, 1, 10001, 25),
  (4000001, 3000003, 1, 10001, 30);

-- 9. Insert Enrollments
-- Enroll each student in at least one current course offering:
-- INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
-- VALUES
  -- Department 1 current enrollments
  -- (5000002, 2000001, 4000002, '2025-04-10', 'Approved'),
  -- (5000003, 2000002, 4000003, '2025-04-10', 'Approved'),
  -- -- Department 2 current enrollments
  -- (5000004, 2000003, 4000004, '2025-04-10', 'Approved'),
  -- (5000005, 2000004, 4000005, '2025-04-10', 'Approved'),
  -- -- Department 3 current enrollments
  -- (5000006, 2000005, 4000006, '2025-04-10', 'Approved'),
  -- (5000007, 2000006, 4000007, '2025-04-10', 'Approved');

-- Additionally, enroll student 201 in the past term course offering (for a completed course)
INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
VALUES
  (5000001, 2000001, 4000001, '2024-09-05', 'Approved'),
  (5000002, 2000001, 4000000, '2024-09-05', 'Approved');

-- 10. Insert Student Grades for the completed enrollment from the past term
INSERT INTO StudentGrades (enrollmentId, grade, remarks)
VALUES
  (5000001, 85.50, 'Good performance'),
  (5000002, 90.00, 'Top of the Class');

-- 11. Insert UserLogins
INSERT INTO UserLogin (role, userId, password)
VALUES
  ('student', 2000001, '2000001'),
  ('student', 2000002, '2000002'),
  ('student', 2000003, '2000003'),
  ('student', 2000004, '2000004'),
  ('student', 2000005, '2000005'),
  ('student', 2000006, '2000006'),
  ('professor', 10001, '10001'),
  ('professor', 10002, '10002'),
  ('professor', 10003, '10003'),
  ('admin', 9999999, '9999999');

CREATE OR REPLACE FUNCTION get_registration_log(
    p_student_id INT,
    p_term_id    INT
)
RETURNS TABLE (
    "offeringId"     INT,
    "courseId"       INT,
    "courseName"     VARCHAR,
    "credits"        INT,
    "deptName"       VARCHAR,
    "termName"       VARCHAR,
    "professorName"  VARCHAR,
    "courseType"     TEXT,
    "status"         VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_stud_dept INT;
BEGIN
    SELECT departmentId
      INTO v_stud_dept
      FROM Students
     WHERE studentId = p_student_id;

    RETURN QUERY
    SELECT
      co.offeringId,
      c.courseId,
      c.courseName,
      c.credits,
      d.deptName,
      at.termName,
      p.professorName,
      CASE
        WHEN c.departmentId = v_stud_dept THEN 'Core Course'
        ELSE 'Elective Course'
      END,
      e.status
    FROM Enrollment e
    JOIN CourseOffering co ON e.offeringId = co.offeringId
    JOIN Courses        c  ON co.courseId    = c.courseId
    JOIN Department     d  ON c.departmentId = d.departmentId
    JOIN AcademicTerm   at ON co.termId       = at.termId
    JOIN Professors     p  ON co.professorId  = p.professorId
    WHERE e.studentId = p_student_id
      AND co.termId    = p_term_id;
END;
$$;

CREATE OR REPLACE VIEW vw_student_course_overview AS
SELECT
  e.studentId      AS student_id,
  co.termId        AS term_id,
  co.offeringId    AS offering_id,
  c.courseId       AS course_id,
  c.courseName     AS course_name,
  c.credits        AS credits,
  d.deptName       AS dept_name,
  at.termName      AS term_name,
  p.professorName  AS professor_name,
  CASE
    WHEN c.departmentId = s.departmentId THEN 'Core Course'
    ELSE 'Elective Course'
  END               AS course_type,
  e.status         AS status
FROM Enrollment     e
JOIN Students       s  ON e.studentId    = s.studentId
JOIN CourseOffering co ON e.offeringId   = co.offeringId
JOIN Courses        c  ON co.courseId    = c.courseId
JOIN Department     d  ON c.departmentId = d.departmentId
JOIN AcademicTerm   at ON co.termId       = at.termId
JOIN Professors     p  ON co.professorId  = p.professorId;

CREATE OR REPLACE FUNCTION get_approved_courses_from_view(
  p_student_id  INT,
  p_term_id     INT
)
RETURNS TABLE (
  "offeringId"    INT,
  "courseId"      INT,
  "courseName"    VARCHAR,
  "credits"        INT,
  "deptName"      VARCHAR,
  "termName"      VARCHAR,
  "professorName" VARCHAR,
  "courseType"    TEXT
)
LANGUAGE sql
AS $$
  SELECT
    offering_id,
    course_id,
    course_name,
    credits,
    dept_name,
    term_name,
    professor_name,
    course_type
  FROM vw_student_course_overview
  WHERE student_id = p_student_id
    AND term_id    = p_term_id
    AND status     = 'Approved'
  ORDER BY course_name;
$$;

CREATE OR REPLACE FUNCTION getAddDropCourses(
    p_student_id INT,
    p_term_id    INT
)
RETURNS TABLE (
    "offeringId"       INT,
    "courseId"         INT,
    "courseName"       VARCHAR,
    "credits"          INT,
    "deptName"         VARCHAR,
    "termName"         VARCHAR,
    "professorName"    VARCHAR,
    "courseType"       TEXT,
    "enrollmentStatus" VARCHAR,
    "previousTermName" VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_stud_dept INT;
    v_stud_type CHAR(2);
BEGIN
    -- 1) fetch student’s home department
    SELECT departmentId
      INTO v_stud_dept
      FROM Students
     WHERE studentId = p_student_id;

    -- 2) fetch whether student is UG or PG
    SELECT d.ugPgType
      INTO v_stud_type
      FROM Students s
      JOIN Degree   d ON s.degreeId = d.degreeId
     WHERE s.studentId = p_student_id;

    -- 3) only return courses matching that UG/PG type
    RETURN QUERY
    SELECT
        co.offeringId,
        c.courseId,
        c.courseName,
        c.credits,
        d.deptName,
        at.termName,
        p.professorName,
        CASE
          WHEN c.departmentId = v_stud_dept THEN 'Core Course'
          ELSE 'Elective Course'
        END,
        -- current enrollment status (NULL if never enrolled)
        (SELECT e.status
           FROM Enrollment e
          WHERE e.studentId  = p_student_id
            AND e.offeringId = co.offeringId),
        -- last term they passed this course (grade > 35), if any
        (SELECT at2.termName
           FROM Enrollment    e2
           JOIN CourseOffering co2 ON e2.offeringId = co2.offeringId
           JOIN AcademicTerm   at2 ON co2.termId     = at2.termId
           JOIN StudentGrades  sg2 ON e2.enrollmentId = sg2.enrollmentId
          WHERE e2.studentId  = p_student_id
            AND co2.courseId  = c.courseId
            AND e2.status     = 'Approved'
            AND sg2.grade    > 35
          ORDER BY at2.startDate DESC
          LIMIT 1)
    FROM CourseOffering co
    JOIN Courses       c  ON co.courseId    = c.courseId
    JOIN Department    d  ON c.departmentId = d.departmentId
    JOIN AcademicTerm  at ON co.termId       = at.termId
    JOIN Professors    p  ON co.professorId  = p.professorId
    WHERE co.termId       = p_term_id
      AND c.typeOfCourse  = v_stud_type   -- <-- match UG/PG
    ORDER BY d.departmentId,
             c.courseName,
             at.termId;
END;
$$;

-- 1) Trigger function: checks total pending credits + this new course
CREATE OR REPLACE FUNCTION check_pending_credits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  existing_credits INT;
  this_credit INT;
  this_term INT;
BEGIN
  -- Only enforce on rows that are (about to be) Pending
  IF (TG_OP = 'INSERT' AND NEW.status = 'Pending')
     OR (TG_OP = 'UPDATE' AND NEW.status = 'Pending' AND OLD.status <> 'Pending') THEN

    -- Get the term of the offering being added
    SELECT co.termId, c.credits
      INTO this_term, this_credit
    FROM CourseOffering co
    JOIN Courses c ON co.courseId = c.courseId
    WHERE co.offeringId = NEW.offeringId;

    -- Sum up all pending credits for the same student and same term
    SELECT COALESCE(SUM(c.credits), 0)
      INTO existing_credits
    FROM Enrollment e
    JOIN CourseOffering co ON e.offeringId = co.offeringId
    JOIN Courses c ON co.courseId = c.courseId
    WHERE e.studentId = NEW.studentId
      AND e.status = 'Pending'
      AND co.termId = this_term;

    -- Total including the current one
    IF existing_credits + this_credit > 24 THEN
      RAISE EXCEPTION
        'Enrollments pending (current % + this course % = %) exceed 24-credit limit',
        existing_credits, this_credit, existing_credits + this_credit;
    END IF;
  END IF;

  RETURN NEW;
END;
$$;

-- 2) Attach it as a BEFORE INSERT/UPDATE trigger on Enrollment

CREATE TRIGGER trg_check_pending_credits
  BEFORE INSERT OR UPDATE ON Enrollment
  FOR EACH ROW
  EXECUTE FUNCTION check_pending_credits();
