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


CREATE SEQUENCE offering_id_seq START WITH 4000001 INCREMENT BY 1;
CREATE TABLE CourseOffering (
  offeringId INT NOT NULL PRIMARY KEY DEFAULT nextval('offering_id_seq'),
  courseId int NOT NULL,
  termId int NOT NULL,
  professorId int NOT NULL,
  maxCapacity int NOT NULL CHECK (maxCapacity > 0)
);

CREATE TABLE  (
  enrollmentI int PRIMARY KEY,
  studentId it NOT NULL,
  offeringId nt NOT NULL,
  enrollmentDate dte NOT NULL,
  status varcar(20) CHECK (status IN ('Approved', 'Rejected', 'Pending', 'Dropped')),
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
ALTER TABLE  ADD FOREIGN KEY (studentId) REFERENCES Students(studentId);
ALTER TABLE ADD FOREIGN KEY (offeringId) REFERENCES CourseOffering(offeringId);
ALTER TABLE udentGrades ADD FOREIGN KEY (enrollmentId) REFERENCES (enrollmentId);
NSERT INTO Dgree (degreeId, degreeName, ugPgType, maxYears, totalCreditsRequired, coreCreditsRequired)
ALUES 
  (1'B.Tech', 'UG', 4, 160, 100),  (2, 'M.Tech', 'PG', 2, 60, 40);

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
INSERT INTO  (enrollmentId, studentId, offeringId, enrollmentDate, status)
VALUES  -- Department 1 current enrollments
  (500001, 2000001, 4000001, '2025-04-10', 'Approved'),
  (500002, 2000002, 4000002, '2025-04-10', 'Approved'),
  (5000003,2000003, 4000003, '2025-04-10', 'Approved'),
  (500004, 2000004, 4000004, '2025-04-10', 'Approved'),
  (5000005, 2000005, 4000005, '2025-04-10', 'Approved'),
  (5000006, 2000006, 4000006, '2025-04-10', 'Approved');

-- Additionally, enroll student 201 in the past term course offering (for a completed course)
INSERT INTO  (enrollmentId, studentId, offeringId, enrollmentDate, status)
VALUES  (5000007, 2000001, 4000007, '2024-09-05', 'Approved');
-- 10. Insert Student Grades for the completed enrollment from the past term
NSERT INTO StudentGrades (enrollmentId, grade, remarks)
VALUE
 (5000007, 85.50, 'Good performance'),
  (5000001,  0.00, 'Null'),
  (5000002,  0.00, 'Null'),
  (5000003,  0.00, 'Null'),
  (5000004,  0.00, 'Null'),
  (5000005,  0.00, 'Null'),
  (5000006,  0.00, 'Null');
  

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


CREATE ROLE admin;
CREATE ROLE student;
CREATE ROLE professor;

-- Grant all privileges to admin on all tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- Grant select on all tables to all roles
GRANT SELECT ON ALL TABLES IN SCHEMA public TO student, professor, admin;

-- Professor privileges
GRANT INSERT ON TABLE CourseOffering TO professor;
GRANT UPDATE ON TABLE  TO professor;
GRANT INSERT, UPDATE O TABLE StudentGrades TO professor;
-- Student privileges
RANT INSERT, UPDATE ON TABLE  TO student;
-- Reoke privileges on UserLogin table for non-admin roles
VOKE ALL PRIVILEGES ON TABLE UserLogin FROM student, professor;
RANT SELECT ON TABLE UserLogin TO student, professor;
GRANTUSAGE ON SCHEMA public TO admin, professor, studnt;


--admin level functions

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

-- Function to generate the next course ID
CREATE OR REPLACE FUNCTION get_next_course_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    -- Start IDs from 3000001 based on your sample data, or use MAX + 1
    SELECT COALESCE(MAX(courseId), 3000000) + 1 INTO next_id FROM Courses;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert a new course
CREATE OR REPLACE PROCEDURE insert_course(
    p_courseName VARCHAR(100),
    p_departmentId INT,
    p_typeOfCourse VARCHAR(2), -- UG/PG
    p_courseType VARCHAR(20),  -- Theory/Lab
    p_credits INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_courseId INT;
BEGIN
    -- Optional: Add specific validation if needed, beyond table constraints
    -- Example: Check if department exists (though FK constraint handles this)
    -- IF NOT EXISTS (SELECT 1 FROM Department WHERE departmentId = p_departmentId) THEN
    --     RAISE EXCEPTION 'Department with ID % does not exist.', p_departmentId;
    -- END IF;

    -- Get next available course ID
    v_courseId := get_next_course_id();

    -- Insert into Courses table
    INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, courseType, credits)
    VALUES (v_courseId, p_courseName, p_departmentId, p_typeOfCourse, p_courseType, p_credits);
END;
$$;

CREATE OR REPLACE PROCEDURE assign_hod(
    p_departmentId INT,
    p_professorId INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_prof_dept_id INT;
    v_prof_status VARCHAR(10);
BEGIN
    -- 1. Check if the chosen professor exists, is active, and get their department
    SELECT departmentId, WorkingStatus
    INTO v_prof_dept_id, v_prof_status
    FROM Professors
    WHERE professorId = p_professorId;

    -- Raise error if professor not found or not active
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Professor with ID % does not exist.', p_professorId;
    END IF;

    IF v_prof_status <> 'Active' THEN
        RAISE EXCEPTION 'Professor % is not currently Active (Status: %).', p_professorId, v_prof_status;
    END IF;

    -- 2. Check if the professor belongs to the target department
    IF v_prof_dept_id <> p_departmentId THEN
        RAISE EXCEPTION 'Professor % does not belong to Department %.', p_professorId, p_departmentId;
    END IF;

    -- 3. Update the Department table
    UPDATE Department
    SET headOfDeptId = p_professorId
    WHERE departmentId = p_departmentId;

    -- Check if the update was successful (optional, department might not exist)
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Department with ID % does not exist.', p_departmentId;
    END IF;

END;
$$;



CREATE OR REPLACE FUNCTION get_student_passed_core_credits(p_studentId INT)
RETURNS INT AS $$
DECLARE
    total_core_credits INT;
    v_student_dept_id INT;
BEGIN
    -- Get the student's department first
    SELECT departmentId INTO v_student_dept_id FROM Students WHERE studentId = p_studentId;

    IF NOT FOUND THEN
        RETURN 0; -- Student not found
    END IF;

    -- Sum credits from passed courses within the student's department
    SELECT COALESCE(SUM(c.credits), 0)
    INTO total_core_credits
    FROM  e
    JOIN tudentGrades sg ON e.enrollmentId = sg.enrollmentId
    JOIN ourseOffering co ON e.offeringId = co.offeringId
    JOIN ourses c ON co.courseId = c.courseId
    WHERE e.stdentId = p_studentId
      ANDsg.grade >= 50.00 -- Assuming 50 is the passing grade threshold
      AND c.departmentId = v_student_dept_id; -- Core course condition

    RETURN total_core_credits;
END;
$$ LANGUAGE plpgsql;

--professor level functions
CREATE OR REPLACE FUNCTION CheckCourseCapacity(p_offering_id INT)
RETURNS BOOLEAN AS $$
DECLARE
    v_max_capacity INT;
    v_current_enrollment INT;
BEGIN
    -- Get the max capacity for the offering
    SELECT maxCapacity INTO v_max_capacity
    FROM CourseOffering
    WHERE offeringId = p_offering_id;
    
    -- If offering not found, return false
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Get the current count of *approved* students
    SELECT COUNT(*) INTO v_current_enrollment
    FROM 
    WHEREofferingId = p_offering_id AND status = 'Approved';
        -- Check if adding one more student exceeds capacity
    ETURN (v_current_enrollment < v_max_capacity);
END;
$$ LNGUAGE plpgql;


CREATE OR REPLACE FUNCTION AddStudentGradeOnApproval()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the status column was updated to 'Approved'
    IF TG_OP = 'UPDATE' AND NEW.status = 'Approved' AND OLD.status <> 'Approved' THEN
        -- Insert a corresponding record into StudentGrades with NULL grade initially
        INSERT INTO StudentGrades (enrollmentId, grade, remarks)
        VALUES (NEW.enrollmentId, 0, 'Automatically created upon enrollment approval');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the trigger if it exists to avoid errors
-- DROP TRIGGER IF EXISTS trg_Enrollment_AfterUpdate_AddGrade ON ;
-- Create the trigger
REATE OR REPLACE TRIGGER trg_Enrollment_AfterUpdate_AddGrade
FTER UPDATE ON 
FOR ECH ROWEXECUTE FUNCTION AddStudentGradeOnApproval();
- Function to calculate the average grade for a course offering
REATE OR REPLACE FUNCTION GetCourseAverageGrade (p_offering_id INT)
RETURS DOUBLE PRECISION -- Or NUMERIC for exact precision
S $$
DECLARE
    avg_grade DOUBLE PRECISION;
BEGIN
    SELECT AVG(sg.grade)
    INTO avg_grade
    FROM StudentGrades sg
    JOIN  e ON sg.enrollmentId = e.enrollmentId
    WHEREe.offeringId = p_offering_id
      ANDe.status = 'Approved'
      ANDsg.grade IS NOT NULL;

    ETURN avg_grade; -- Returns NULL if no non-null grades foundEND;
$$ LANGUAGE plpgsql;

-- Function to calculate the sample standard deviation for a course offering
CREATE OR REPLACE FUNCTION GetCourseStdDevGrade (p_offering_id INT)
RETURNS DOUBLE PRECISION -- Or NUMERIC
AS $$
DECLARE
    stddev_grade DOUBLE PRECISION;
BEGIN
    SELECT STDDEV_SAMP(sg.grade) -- Standard sample deviation
    INTO stddev_grade
    FROM StudentGrades sg
    JOIN  e ON sg.enrollmentId = e.enrollmentId
    WHEREe.offeringId = p_offering_id
      ANDe.status = 'Approved'
      ANDsg.grade IS NOT NULL;

    ETURN stddev_grade; -- Returns NULL if count is 0 or 1END;
$$ LANGUAGE plpgsql;

-- Function to count graded students (Optional but good practice)
CREATE OR REPLACE FUNCTION CountGradedStudents (p_offering_id INT)
RETURNS INTEGER
AS $$
DECLARE
    grade_count INTEGER;
BEGIN
    SELECT COUNT(sg.grade)
    INTO grade_count
    FROM StudentGrades sg
    JOIN  e ON sg.enrollmentId = e.enrollmentId
    WHEREe.offeringId = p_offering_id
      ANDe.status = 'Approved'
      ANDsg.grade IS NOT NULL;

    ETURN grade_count;END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE VIEW vw_ProfessorCourseDetails AS
SELECT 
    c.courseId AS "courseId", 
    c.courseName AS "courseName", 
    c.credits AS "credits", 
    d.deptName AS "deptName", 
    at.termName AS "termName",
    at.termId AS "termId",
    p.professorId AS "professorId", 
    c.coursetype AS "courseType",
    e.studentId AS "studentId" 
FROM  e
JOIN ourseOffering co ON e.offeringId = co.offeringId
JOIN ourses c ON co.courseId = c.courseId
JOIN epartment d ON c.departmentId = d.departmentId
JOIN AcadeicTerm at ON co.termId = at.termId
JOIN rofessors p ON co.professorId = p.professorId;

--student level functions
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
    FROM  e
    JOIN ourseOffering co ON e.offeringId = co.offeringId
    JOIN ourses        c  ON co.courseId    = c.courseId
    JOIN epartment     d  ON c.departmentId = d.departmentId
    JOIN AcadeicTerm   at ON co.termId       = at.termId
    JOIN rofessors     p  ON co.professorId  = p.professorId
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
FROM      e
JOIN tudents       s  ON e.studentId    = s.studentId
JOIN ourseOffering co ON e.offeringId   = co.offeringId
JOIN ourses        c  ON co.courseId    = c.courseId
JOIN Deparment     d  ON c.departmentId = d.departmentId
JOIN cademicTerm   at ON co.termId       = at.termId
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
           FROM  e
          WHERE .studentId  = p_student_id
            AND .offeringId = co.offeringId),
        -- last erm they passed this course (grade > 35), if any
        (SELECT at2.trmName
           FROM    e2
           JOIN ourseOffering co2 ON e2.offeringId = co2.offeringId
           JOIN cademicTerm   at2 ON co2.termId     = at2.termId
           JOIN tudentGrades  sg2 ON e2.enrollmentId = sg2.enrollmentId
          WHERE e2.stdentId  = p_student_id
            AND o2.courseId  = c.courseId
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
    FROM  e
    JOIN ourseOffering co ON e.offeringId = co.offeringId
    JOIN ourses c ON co.courseId = c.courseId
    WHEREe.studentId = NEW.studentId
      AND e.sttus = 'Pending'
      ANDco.termId = this_term;

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

-- 2) Attach it as a BEFORE INSERT/UPDATE trigger on 
CREATE TRIGGER trg_check_pending_credits
 BEFORE INSERT OR UPDATE ON 
 FOR EACH ROW  EXECUTE FUNCTION check_pending_credits();
-- Fuction to check if adding a new term is allowed
 Returns TRUE if allowed, FALSE otherwise
CREAT OR REPLACE FUNCTION can_add_new_term()
ETURNS BOOLEAN AS $$
DECLARE
    v_latest_endDate DATE;
BEGIN
    -- Find the end date of the term with the highest ID (most recently added)
    SELECT endDate
    INTO v_latest_endDate
    FROM AcademicTerm
    ORDER BY termId DESC -- Assuming higher termId means later term
    LIMIT 1;

    -- If no terms exist yet, allow adding the first one
    IF NOT FOUND THEN
        RETURN TRUE;
    END IF;

    -- Allow adding if the current date is past the latest term's end date
    IF CURRENT_DATE > v_latest_endDate THEN
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Function to get the next term ID (unchanged from previous example)
CREATE OR REPLACE FUNCTION get_next_term_id()
RETURNS INT AS $$
DECLARE
    next_id INT;
BEGIN
    SELECT COALESCE(MAX(termId), 0) + 1 INTO next_id FROM AcademicTerm;
    RETURN next_id;
END;
$$ LANGUAGE plpgsql;


-- Procedure to insert a new term (validation simplified, relies on application check)
CREATE OR REPLACE PROCEDURE insert_academic_term(
    p_termName VARCHAR(50),
    p_startDate DATE,
    p_endDate DATE
)
LANGUAGE plpgsql AS $$
DECLARE
    v_termId INT;
BEGIN
    -- Basic date validation (should also be done in application)
    IF p_endDate <= p_startDate THEN
        RAISE EXCEPTION 'End date (%) must be after start date (%).', p_endDate, p_startDate;
    END IF;

    -- Get the next term ID
    v_termId := get_next_term_id();

    -- Insert the new term
    INSERT INTO AcademicTerm (termId, termName, startDate, endDate)
    VALUES (v_termId, p_termName, p_startDate, p_endDate);
END;
$$;

-- 1) VIEW: flatten +Grades+Course+Dept+Prof + compute letter & points
CREATE OR REPLACE VIEW student_grade_details AS
SELECT  e.studentId     AS student_id,
  co.termId       AS term_id,
  c.courseId      AS course_id,
  c.courseName    AS course_name,
  c.credits       AS credits,
  d.deptName      AS dept_name,
  p.professorName AS professor_name,
  e.status        AS status,
  sg.grade        AS marks,
  CASE
    WHEN sg.grade BETWEEN 91 AND 100 THEN 'S'
    WHEN sg.grade BETWEEN 81 AND  90 THEN 'A'
    WHEN sg.grade BETWEEN 71 AND  80 THEN 'B'
    WHEN sg.grade BETWEEN 61 AND  70 THEN 'C'
    WHEN sg.grade BETWEEN 51 AND  60 THEN 'D'
    WHEN sg.grade BETWEEN 35 AND  50 THEN 'E'
    ELSE 'F'
  END                AS letter_grade,
  CASE
    WHEN sg.grade BETWEEN 91 AND 100 THEN 10
    WHEN sg.grade BETWEEN 81 AND  90 THEN 9
    WHEN sg.grade BETWEEN 71 AND  80 THEN 8
    WHEN sg.grade BETWEEN 61 AND  70 THEN 7
    WHEN sg.grade BETWEEN 51 AND  60 THEN 6
    WHEN sg.grade BETWEEN 35 AND  50 THEN 5
    ELSE 0
  END                AS grade_point,
  c.courseType    AS course_type
FROM Enrollment e
JOIN CourseOffering co       ON e.offeringId  = co.offeringId
JOIN Courses c               ON co.courseId    = c.courseId
JOIN Department d            ON c.departmentId = d.departmentId
LEFT JOIN StudentGrades sg   ON e.enrollmentId = sg.enrollmentId
JOIN Professors p            ON co.professorId = p.professorId
WHERE e.status = 'Approved'
;

-- 2) FUNCTION: get all approved grades for a given student & term
CREATE OR REPLACE FUNCTION get_term_grades(
  p_student_id INT,
  p_term_id    INT
) RETURNS TABLE (
  "course_id"      INT,
  "course_name"    VARCHAR,
  "credits"        INT,
  "dept_name"      VARCHAR,
  "professor_name" VARCHAR,
  "marks"          NUMERIC,
  "letter_grade"   VARCHAR,
  "grade_point"    INT,
  "course_type"    VARCHAR
) AS $$
  SELECT 
    course_id, course_name, credits, dept_name, professor_name,
    marks, letter_grade, grade_point, course_type
  FROM student_grade_details
  WHERE student_id = p_student_id
    AND term_id    = p_term_id
    AND status     = 'Approved'
  ORDER BY course_id;
$$ LANGUAGE sql STABLE;

-- 3) FUNCTION: compute SGPA for one term
CREATE OR REPLACE FUNCTION get_sgpa(
  p_student_id INT,
  p_term_id    INT
) RETURNS NUMERIC AS $$
  SELECT ROUND(
    SUM(credits * grade_point)::numeric
    / NULLIF(SUM(credits),0),
    2
  )
  FROM student_grade_details
  WHERE student_id = p_student_id
    AND term_id    = p_term_id
$$ LANGUAGE sql STABLE;

-- 4) FUNCTION: compute CGPA up to and including that term
CREATE OR REPLACE FUNCTION get_cgpa(
  p_student_id INT,
  p_term_id    INT
) RETURNS NUMERIC AS $$
  SELECT ROUND(
    SUM(credits * grade_point)::numeric
    / NULLIF(SUM(credits),0),
    2
  )
  FROM student_grade_details
  WHERE student_id = p_student_id
    AND term_id   <= p_term_id
$$ LANGUAGE sql STABLE;
