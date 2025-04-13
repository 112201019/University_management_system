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
  gender varchar(10) CHECK (gender IN ('Male', 'Female', 'Other'))
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
  graduationStatus varchar(20) CHECK(graduationStatus in ('Graduated','In Progress','Discontinued', 'Max years exceeded'))
);

CREATE TABLE Courses (
  courseId int PRIMARY KEY,
  courseName varchar(100) NOT NULL,
  departmentId int NOT NULL, -- Renamed from deptId
  typeOfCourse varchar(2) NOT NULL CHECK (typeOfCourse IN ('UG', 'PG')),
  professorId int NOT NULL,
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
  status varchar(20) CHECK (status IN ('Approved', 'Rejected', 'Pending')),
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
INSERT INTO Professors (professorId, departmentId, professorName, dob, gender)
VALUES 
  (10001, 1, 'Dr. Alice', '1975-06-15', 'Female'),
  (10002, 2, 'Dr. Bob', '1980-09-20', 'Male'),
  (10003, 3, 'Dr. Carol', '1978-04-10', 'Female');

-- 4. Update Departments to assign headOfDeptId from the corresponding professor
UPDATE Department SET headOfDeptId = 10001 WHERE departmentId = 1;
UPDATE Department SET headOfDeptId = 10002 WHERE departmentId = 2;
UPDATE Department SET headOfDeptId = 10003 WHERE departmentId = 3;

-- 5. Insert Students
INSERT INTO Students (studentId, studentName, degreeId, departmentId, dateOfJoining, gender, dob, graduated)
VALUES 
  -- Department 1: Computer Science Engineering (all B.Tech)
  (2000001, 'John Doe', 1, 1, '2023-08-15', 'Male', '2005-05-12', 0),
  (2000002, 'Jane Smith', 1, 1, '2023-08-15', 'Female', '2005-11-30', 0),

  -- Department 2: Data Science Engineering (mix of B.Tech and M.Tech)
  (2000003, 'Mike Brown', 1, 2, '2023-08-15', 'Male', '2005-03-22', 0),
  (2000004, 'Emily White', 2, 2, '2024-01-10', 'Female', '2002-12-05', 0),

  -- Department 3: Electrical Engineering (all B.Tech)
  (2000005, 'Robert Green', 1, 3, '2023-08-15', 'Male', '2005-07-07', 0),
  (2000006, 'Linda Blue', 1, 3, '2023-08-15', 'Female', '2005-09-15', 0);

-- 6. Insert Courses
-- Department 1 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, professorId, courseType, credits)
VALUES
  (3000001, 'Introduction to Programming', 1, 'UG', 10001, 'Theory', 4),
  (3000002, 'Data Structures', 1, 'UG', 10001, 'Theory', 4),
  (3000003, 'Programming Lab', 1, 'UG', 10001, 'Lab', 2);

-- Department 2 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, professorId, courseType, credits)
VALUES
  (3000004, 'Statistics for Data Science', 2, 'UG', 10002, 'Theory', 3),
  (3000005, 'Machine Learning Basics', 2, 'UG', 10002, 'Theory', 4),
  (3000006, 'Data Science Lab', 2, 'UG', 10002, 'Lab', 2);

-- Department 3 Courses
INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, professorId, courseType, credits)
VALUES
  (3000007, 'Circuits and Electronics', 3, 'UG', 10003, 'Theory', 4),
  (3000008, 'Electrical Machines', 3, 'UG', 10003, 'Theory', 4),
  (3000009, 'Electronics Lab', 3, 'UG', 10003, 'Lab', 2);

-- 7. Insert Academic Terms
-- Ongoing term (Spring 2025: current date 2025-04-11 falls between start and end dates)
INSERT INTO AcademicTerm (termId, termName, startDate, endDate)
VALUES 
  (1, 'Spring 2025', '2025-01-10', '2025-05-20');

-- An additional past term to support a completed enrollment and grade (Fall 2024)
INSERT INTO AcademicTerm (termId, termName, startDate, endDate)
VALUES 
  (2, 'Fall 2024', '2024-09-01', '2024-12-15');

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
  ('student', 2000007, '2000007'),
  ('student', 2000008, '2000008'),
  ('professor', 10001, '10001'),
  ('professor', 10002, '10002'),
  ('professor', 10003, '10003'),
  ('admin', 9999999, '9999999');

CREATE ROLE student;
CREATE ROLE professor;
CREATE ROLE admin;
