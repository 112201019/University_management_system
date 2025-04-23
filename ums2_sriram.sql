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
  (3000003, 'Programming Lab', 1, 'UG', 'Lab', 2);

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
-- Ongoing semester offerings (termId = 1)
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  -- For Department 1
  (4000001, 3000001, 2, 10001, 30),
  (4000002, 3000002, 2, 10001, 30),
  -- For Department 2
  (4000003, 3000004, 2, 10002, 25),
  (4000004, 3000005, 2, 10002, 25),
  -- For Department 3
  (4000005, 3000007, 2, 10003, 20),
  (4000006, 3000008, 2, 10003, 20);

-- Past term offering (termId = 2) to demonstrate StudentGrades entry.
INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
VALUES
  (4000007, 3000003, 1, 10001, 30);

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
    INSERT INTO Professors (professorId, professorName, departmentId, dob, gender, WorkingStatus)
    VALUES (v_professorId, p_professorName, p_departmentId, p_dob, p_gender, 'Active');
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
-----------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE delete_student(p_student_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Students
    SET graduationStatus = 'Discontinued'
    WHERE studentId = p_student_id;

END;
$$;

CREATE OR REPLACE FUNCTION handle_discontinued_student_login()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.graduationStatus = 'Discontinued' AND OLD.graduationStatus IS DISTINCT FROM 'Discontinued' THEN
        DELETE FROM UserLogin WHERE userId = OLD.studentId AND role = 'student';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER student_status_update_trigger
AFTER UPDATE OF graduationStatus ON Students
FOR EACH ROW
WHEN (NEW.graduationStatus = 'Discontinued' AND OLD.graduationStatus IS DISTINCT FROM 'Discontinued')
EXECUTE FUNCTION handle_discontinued_student_login();

-- Modified procedure to update status instead of deleting
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
        RAISE EXCEPTION 'Cannot mark professor as departed. They are currently assigned as a department head.';
    END IF;

    -- Update the professor's status to 'Departed' if not a department head
    UPDATE Professors
    SET WorkingStatus = 'Departed'
    WHERE professorId = p_professor_id;

    -- Note: The UserLogin deletion will be handled by the updated trigger
END;
$$;

-- Trigger function to handle login deletion upon status change
CREATE OR REPLACE FUNCTION handle_departed_professor_login()
RETURNS TRIGGER AS $$
BEGIN
    -- This function is called when the WHEN condition in the trigger is met.
    -- It deletes the login for the professor whose status just changed to 'Departed'.
    DELETE FROM UserLogin WHERE userId = OLD.professorId AND role = 'professor';
    RETURN OLD; -- Return value ignored for AFTER triggers, but required syntax.
END;
$$ LANGUAGE plpgsql;


-- Create the new trigger for UPDATE events on WorkingStatus
CREATE TRIGGER professor_status_update_trigger -- New descriptive name
AFTER UPDATE OF WorkingStatus ON Professors -- Fire specifically when WorkingStatus might have changed
FOR EACH ROW
-- Only execute the function if the status actually changed TO 'Departed'
WHEN (NEW.WorkingStatus = 'Departed' AND OLD.WorkingStatus IS DISTINCT FROM 'Departed')
EXECUTE FUNCTION handle_departed_professor_login(); -- Call the function to delete the login



-- Function to generate the next department ID
CREATE OR REPLACE FUNCTION get_next_department_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    -- Start IDs from 1, or use the next available after the max
    SELECT COALESCE(MAX(departmentId), 0) + 1 INTO next_id FROM Department;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert a new department
CREATE OR REPLACE PROCEDURE insert_department(
    p_deptName VARCHAR(100)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_departmentId INT;
BEGIN
    -- Get next available department ID
    v_departmentId := get_next_department_id();

    -- Insert into Department table, headOfDeptId is NULL initially
    INSERT INTO Department (departmentId, deptName, headOfDeptId)
    VALUES (v_departmentId, p_deptName, NULL);

    -- Optionally, you could return the new ID if needed, but procedures don't return values directly.
    -- You might use an INOUT parameter if the ID needs to be passed back.
END;
$$;

-- Function to generate the next degree ID
CREATE OR REPLACE FUNCTION get_next_degree_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    -- Start IDs from 1, or use the next available after the max
    SELECT COALESCE(MAX(degreeId), 0) + 1 INTO next_id FROM Degree;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert a new degree
CREATE OR REPLACE PROCEDURE insert_degree(
    p_degreeName VARCHAR(100),
    p_ugPgType VARCHAR(2),
    p_maxYears INT,
    p_totalCreditsRequired INT,
    p_coreCreditsRequired INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_degreeId INT;
BEGIN
    -- Validate core credits against total credits before inserting
    IF p_coreCreditsRequired > p_totalCreditsRequired THEN
        RAISE EXCEPTION 'Core credits required (%) cannot exceed total credits required (%).', p_coreCreditsRequired, p_totalCreditsRequired;
    END IF;

    -- Get next available degree ID
    v_degreeId := get_next_degree_id();

    -- Insert into Degree table
    INSERT INTO Degree (degreeId, degreeName, ugPgType, maxYears, totalCreditsRequired, coreCreditsRequired)
    VALUES (v_degreeId, p_degreeName, p_ugPgType, p_maxYears, p_totalCreditsRequired, p_coreCreditsRequired);
END;
$$;

-- Function to get detailed course offerings for a specific term
CREATE OR REPLACE FUNCTION get_course_offerings_by_term(p_termId INT)
RETURNS TABLE (
    offering_id INT,
    course_id INT,
    course_name VARCHAR(100),
    course_type VARCHAR(20), -- Theory/Lab
    ug_pg_type VARCHAR(2),   -- UG/PG
    credits INT,
    dept_name VARCHAR(100),
    professor_id INT,
    professor_name VARCHAR(100),
    max_capacity INT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        co.offeringId,
        c.courseId,
        c.courseName,
        c.courseType,
        c.typeOfCourse, -- UG/PG from Courses table
        c.credits,
        d.deptName,
        p.professorId,
        p.professorName,
        co.maxCapacity
    FROM CourseOffering co
    JOIN Courses c ON co.courseId = c.courseId
    JOIN Professors p ON co.professorId = p.professorId
    JOIN Department d ON c.departmentId = d.departmentId
    WHERE co.termId = p_termId
    ORDER BY d.deptName, c.courseName;
END;
$$ LANGUAGE plpgsql;

-- Example Usage (how you'd call it in SQL):
-- SELECT * FROM get_course_offerings_by_term(1); -- Assuming termId 1 exists
