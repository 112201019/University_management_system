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
ALTER TABLE Courses ADD FOREIGN KEY (professorId) REFERENCES Professors(professorId);
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
  (3000003, 'Programming Lab', 1, 'UG', 'Lab', 2);

-- Department 2 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, courseType, credits)
VALUES
  (3000004, 'Statistics for Data Science', 2, 'UG',  'Theory', 3),
  (3000005, 'Machine Learning Basics', 2, 'UG',  'Theory', 4),
  (3000006, 'Data Science Lab', 2, 'UG', 'Lab', 2);

-- Department 3 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, professorId, courseType, credits)
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
-- Ongoing semester offerings (termId = 1)
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  -- For Department 1
  (4000001, 3000001, 1, 10001, 30),
  (4000002, 3000002, 1, 10001, 30),
  -- For Department 2
  (4000003, 3000004, 1, 10002, 25),
  (4000004, 3000005, 1, 10002, 25),
  -- For Department 3
  (4000005, 3000007, 1, 10003, 20),
  (4000006, 3000008, 1, 10003, 20);

-- Past term offering (termId = 2) to demonstrate StudentGrades entry.
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  (4000007, 3000003, 2, 10001, 30);

-- 9. Insert Enrollments
-- Enroll each student in at least one current course offering:
INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
VALUES
  -- Department 1 current enrollments
  (5000001, 2000001, 4000001, '2025-04-10', 'Approved'),
  (5000002, 2000002, 4000002, '2025-04-10', 'Approved'),
  -- Department 2 current enrollments
  (5000003, 2000003, 4000003, '2025-04-10', 'Approved'),
  (5000004, 2000004, 4000004, '2025-04-10', 'Approved'),
  -- Department 3 current enrollments
  (5000005, 2000005, 4000005, '2025-04-10', 'Approved'),
  (5000006, 2000006, 4000006, '2025-04-10', 'Approved');

-- Additionally, enroll student 201 in the past term course offering (for a completed course)
INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
VALUES
  (5000007, 2000001, 4000007, '2024-09-05', 'Approved');

-- 10. Insert Student Grades for the completed enrollment from the past term
INSERT INTO StudentGrades (enrollmentId, grade, remarks)
VALUES
  (5000007, 85.50, 'Good performance');

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

CREATE ROLE student;
CREATE ROLE professor;
CREATE ROLE admin;

-- -- 1. Function to generate the next student ID
-- CREATE OR REPLACE FUNCTION get_next_student_id()
-- RETURNS INT AS $$
-- DECLARE
--     next_id INT;
-- BEGIN
--     SELECT COALESCE(MAX(studentId), 2000000) + 1 INTO next_id FROM Students;
--     RETURN next_id;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 2. Function to insert a new student
-- CREATE OR REPLACE FUNCTION insert_student(
--     p_studentName VARCHAR(100),
--     p_degreeId INT,
--     p_departmentId INT,
--     p_dateOfJoining DATE,
--     p_gender VARCHAR(10),
--     p_dob DATE,
--     p_dateOfGraduation DATE,
--     p_graduationStatus VARCHAR(20)
-- )
-- RETURNS VOID AS $$
-- DECLARE
--     v_studentId INT;
-- BEGIN
--     -- Get next available student ID
--     v_studentId := get_next_student_id();
    
--     -- Insert into Students table
--     INSERT INTO Students (studentId, studentName, degreeId, departmentId, 
--                         dateOfJoining, gender, dob, dateOfGraduation, graduationStatus)
--     VALUES (v_studentId, p_studentName, p_degreeId, p_departmentId, 
--             p_dateOfJoining, p_gender, p_dob, p_dateOfGraduation, p_graduationStatus);
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 3. Trigger function to create login credentials
-- CREATE OR REPLACE FUNCTION create_student_login()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     -- Insert into UserLogin with student ID as password
--     INSERT INTO UserLogin (role, userId, password)
--     VALUES ('student', NEW.studentId, NEW.studentId::VARCHAR);
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 4. Create the trigger
-- CREATE OR REPLACE TRIGGER student_after_insert
-- AFTER INSERT ON Students
-- FOR EACH ROW
-- EXECUTE FUNCTION create_student_login();

-- CREATE OR REPLACE FUNCTION delete_user_credentials()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     DELETE FROM UserLogin WHERE userId = OLD.studentId;
--     RETURN OLD;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 2. Create trigger to execute before student deletion
-- CREATE TRIGGER delete_student_credentials
-- BEFORE DELETE ON Students
-- FOR EACH ROW
-- EXECUTE FUNCTION delete_user_credentials();

-- -- 3. Create delete function for students
-- CREATE OR REPLACE FUNCTION delete_student(p_student_id INT)
-- RETURNS VOID AS $$
-- BEGIN
--     -- First delete grades and enrollments
--     DELETE FROM StudentGrades
--     WHERE enrollmentId IN (
--         SELECT enrollmentId FROM Enrollment WHERE studentId = p_student_id
--     );
    
--     DELETE FROM Enrollment WHERE studentId = p_student_id;
    
--     -- Then delete the student (will trigger login deletion)
--     DELETE FROM Students WHERE studentId = p_student_id;
-- END;
-- $$ LANGUAGE plpgsql;

-- 1. Function to get next student ID
CREATE OR REPLACE FUNCTION get_next_student_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    SELECT COALESCE(MAX(studentId), 2000000) + 1 INTO next_id FROM Students;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- 2. Procedure to insert a student
CREATE OR REPLACE PROCEDURE insert_student(
    p_studentName VARCHAR(100),
    p_degreeId INT,
    p_departmentId INT,
    p_dateOfJoining DATE,
    p_gender VARCHAR(10),
    p_dob DATE,
    p_dateOfGraduation DATE,
    p_graduationStatus VARCHAR(20)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_studentId INT;
BEGIN
    -- Get next available student ID
    v_studentId := get_next_student_id();
    
    -- Insert into Students table
    INSERT INTO Students (studentId, studentName, degreeId, departmentId,
        dateOfJoining, gender, dob, dateOfGraduation, graduationStatus)
    VALUES (v_studentId, p_studentName, p_degreeId, p_departmentId,
        p_dateOfJoining, p_gender, p_dob, p_dateOfGraduation, p_graduationStatus);
END;
$$;

-- 3. Trigger function to add student login credentials
CREATE OR REPLACE FUNCTION create_student_login()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into UserLogin with student ID as password
    INSERT INTO UserLogin (role, userId, password)
    VALUES ('student', NEW.studentId, NEW.studentId::VARCHAR);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create trigger to add login after student insertion
CREATE OR REPLACE TRIGGER student_after_insert
AFTER INSERT ON Students
FOR EACH ROW
EXECUTE FUNCTION create_student_login();

-- 5. Procedure to delete a student
CREATE OR REPLACE PROCEDURE delete_student(p_student_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    -- Delete the student
    DELETE FROM Students WHERE studentId = p_student_id;
END;
$$;

-- 6. Trigger function to delete student login credentials
CREATE OR REPLACE FUNCTION delete_student_login()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete from UserLogin
    DELETE FROM UserLogin WHERE userId = OLD.studentId AND role = 'student';
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 7. Create trigger to delete login after student deletion
CREATE OR REPLACE TRIGGER student_after_delete
AFTER DELETE ON Students
FOR EACH ROW
EXECUTE FUNCTION delete_student_login();

-- -- 1. Function to generate the next professor ID
-- CREATE OR REPLACE FUNCTION get_next_professor_id()
-- RETURNS INT AS $$
-- DECLARE
--     next_id INT;
-- BEGIN
--     SELECT COALESCE(MAX(professorId), 1000000) + 1 INTO next_id FROM Professors;
--     RETURN next_id;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 2. Function to insert a new professor
-- CREATE OR REPLACE FUNCTION insert_professor(
--     p_professorName VARCHAR(100),
--     p_departmentId INT,
--     p_dob DATE,
--     p_gender VARCHAR(10)
-- )
-- RETURNS VOID AS $$
-- DECLARE
--     v_professorId INT;
-- BEGIN
--     -- Get next available professor ID
--     v_professorId := get_next_professor_id();
    
--     -- Insert into Professors table
--     INSERT INTO Professors (professorId, professorName, departmentId, dob, gender)
--     VALUES (v_professorId, p_professorName, p_departmentId, p_dob, p_gender);
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 3. Trigger function to create login credentials
-- CREATE OR REPLACE FUNCTION create_professor_login()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     -- Insert into UserLogin with professor ID as password
--     INSERT INTO UserLogin (role, userId, password)
--     VALUES ('professor', NEW.professorId, NEW.professorId::VARCHAR);
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- -- 4. Create the trigger on Professors table
-- CREATE TRIGGER after_professor_insert
-- AFTER INSERT ON Professors
-- FOR EACH ROW
-- EXECUTE FUNCTION create_professor_login();
-- 1. Function to generate the next professor ID

CREATE OR REPLACE FUNCTION get_next_professor_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    SELECT COALESCE(MAX(professorId), 10000) + 1 INTO next_id FROM Professors;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- 2. Procedure to insert a new professor
CREATE OR REPLACE PROCEDURE insert_professor(
    p_professorName VARCHAR(100),
    p_departmentId INT,
    p_dob DATE,
    p_gender VARCHAR(10)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_professorId INT;
BEGIN
    -- Get next available professor ID
    v_professorId := get_next_professor_id();
    
    -- Insert into Professors table
    INSERT INTO Professors (professorId, professorName, departmentId, dob, gender)
    VALUES (v_professorId, p_professorName, p_departmentId, p_dob, p_gender);
END;
$$;

-- 3. Trigger function to create login credentials
CREATE OR REPLACE FUNCTION create_professor_login()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert into UserLogin with professor ID as password
    INSERT INTO UserLogin (role, userId, password)
    VALUES ('professor', NEW.professorId, NEW.professorId::VARCHAR);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create the trigger on Professors table
CREATE OR REPLACE TRIGGER after_professor_insert
AFTER INSERT ON Professors
FOR EACH ROW
EXECUTE FUNCTION create_professor_login();

-- 5. Procedure to delete a professor
CREATE OR REPLACE PROCEDURE delete_professor(p_professor_id INT)
LANGUAGE plpgsql AS $$
DECLARE
    is_head BOOLEAN;
BEGIN
    -- Check if professor is a department head
    SELECT EXISTS(
        SELECT 1 
        FROM Department 
        WHERE headOfDeptId = p_professor_id
    ) INTO is_head;
    
    -- If professor is a department head, raise an exception
    IF is_head THEN
        RAISE EXCEPTION 'Cannot delete professor. They are currently assigned as a department head.';
    END IF;
    
    -- Delete the professor if not a department head
    DELETE FROM Professors WHERE professorId = p_professor_id;
END;
$$;

-- 6. Trigger function to delete professor login credentials
CREATE OR REPLACE FUNCTION delete_professor_login()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete from UserLogin
    DELETE FROM UserLogin WHERE userId = OLD.professorId AND role = 'professor';
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 7. Create trigger to delete login after professor deletion
CREATE OR REPLACE TRIGGER professor_after_delete
AFTER DELETE ON Professors
FOR EACH ROW
EXECUTE FUNCTION delete_professor_login();