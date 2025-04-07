-- 1. Define tables with corrected data types, checks, and constraints
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
  yearOfJoining int NOT NULL CHECK (yearOfJoining > 1900),
  gender varchar(10) CHECK (gender IN ('Male', 'Female', 'Other')),
  dob date NOT NULL
);

CREATE TABLE Courses (
  courseId int PRIMARY KEY,
  courseName varchar(100) NOT NULL,
  departmentId int NOT NULL, -- Renamed from deptId
  typeOfCourse varchar(2) NOT NULL CHECK (typeOfCourse IN ('UG', 'PG')),
  professorId int NOT NULL,
  courseType varchar(20) CHECK (courseType IN ('Theory', 'Lab')), -- Renamed from 'type'
  credits int NOT NULL CHECK (credits > 0)
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

INSERT INTO Degree (degreeId, degreeName, ugPgType, maxYears, totalCreditsRequired, coreCreditsRequired) VALUES
(1, 'B.Tech Computer Science', 'UG', 4, 180, 120),
(2, 'M.Tech Data Science', 'PG', 2, 90, 60),
(3, 'B.Sc Mathematics', 'UG', 3, 150, 100),
(4, 'MBA Finance', 'PG', 2, 120, 80),
(5, 'B.A English', 'UG', 3, 135, 90),
(6, 'Ph.D Physics', 'PG', 5, 200, 140),
(7, 'B.Com Accounting', 'UG', 3, 150, 100),
(8, 'M.Sc Chemistry', 'PG', 2, 90, 60);

INSERT INTO Department (departmentId, deptName, headOfDeptId) VALUES
(101, 'Computer Science', NULL),
(102, 'Mathematics', NULL),
(103, 'Physics', NULL),
(104, 'Chemistry', NULL),
(105, 'English', NULL),
(106, 'Finance', NULL),
(107, 'Data Science', NULL),
(108, 'Accounting', NULL);

INSERT INTO Professors (professorId, departmentId, professorName, dob, gender) VALUES
(201, 101, 'Dr. Alice Brown', '1975-03-15', 'Female'),
(202, 102, 'Dr. Bob Smith', '1980-07-22', 'Male'),
(203, 103, 'Dr. Carol White', '1978-11-30', 'Other'),
(204, 104, 'Dr. David Lee', '1985-02-14', 'Male'),
(205, 105, 'Dr. Emily Clark', '1990-09-10', 'Female'),
(206, 106, 'Dr. Frank Miller', '1972-12-05', 'Male'),
(207, 107, 'Dr. Grace Hall', '1983-04-18', 'Female'),
(208, 108, 'Dr. Henry Wilson', '1976-06-25', 'Male');

UPDATE Department SET headOfDeptId = 201 WHERE departmentId = 101;
UPDATE Department SET headOfDeptId = 202 WHERE departmentId = 102;
UPDATE Department SET headOfDeptId = 203 WHERE departmentId = 103;
UPDATE Department SET headOfDeptId = 204 WHERE departmentId = 104;
UPDATE Department SET headOfDeptId = 205 WHERE departmentId = 105;
UPDATE Department SET headOfDeptId = 206 WHERE departmentId = 106;
UPDATE Department SET headOfDeptId = 207 WHERE departmentId = 107;
UPDATE Department SET headOfDeptId = 208 WHERE departmentId = 108;

INSERT INTO Students (studentId, studentName, degreeId, departmentId, yearOfJoining, gender, dob) VALUES
(301, 'John Doe', 1, 101, 2020, 'Male', '2002-05-10'),
(302, 'Jane Smith', 2, 107, 2021, 'Female', '1999-08-12'),
(303, 'Ravi Kumar', 3, 102, 2022, 'Male', '2003-01-25'),
(304, 'Priya Patel', 4, 106, 2020, 'Female', '1998-11-30'),
(305, 'Alex Green', 5, 105, 2023, 'Other', '2004-03-15'),
(306, 'Sara Khan', 6, 103, 2019, 'Female', '1997-07-20'),
(307, 'Mike Johnson', 7, 108, 2021, 'Male', '2001-09-05'),
(308, 'Lily Chen', 8, 104, 2022, 'Female', '2000-04-18');

INSERT INTO Courses (courseId, courseName, departmentId, typeOfCourse, professorId, courseType, credits) VALUES
(401, 'Database Systems', 101, 'UG', 201, 'Theory', 4),
(402, 'Linear Algebra', 102, 'UG', 202, 'Theory', 3),
(403, 'Quantum Mechanics', 103, 'PG', 203, 'Theory', 5),
(404, 'Organic Chemistry', 104, 'PG', 204, 'Theory', 4),
(405, 'Shakespeare Studies', 105, 'UG', 205, 'Theory', 3),
(406, 'Financial Management', 106, 'PG', 206, 'Theory', 4),
(407, 'Machine Learning', 107, 'PG', 207, 'Theory', 5),
(408, 'Tax Accounting', 108, 'UG', 208, 'Lab', 4);

INSERT INTO AcademicTerm (termId, termName, startDate, endDate) VALUES
(501, 'Fall 2023', '2023-08-01', '2023-12-15'),
(502, 'Spring 2024', '2024-01-10', '2024-05-20'),
(503, 'Summer 2024', '2024-06-01', '2024-07-31'),
(504, 'Fall 2024', '2024-08-01', '2024-12-15'),
(505, 'Spring 2025', '2025-01-10', '2025-05-20'),
(506, 'Summer 2025', '2025-06-01', '2025-07-31'),
(507, 'Fall 2025', '2025-08-01', '2025-12-15'),
(508, 'Spring 2026', '2026-01-10', '2026-05-20');

INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity) VALUES
(601, 401, 501, 201, 30),
(602, 402, 501, 202, 25),
(603, 403, 502, 203, 20),
(604, 404, 502, 204, 25),
(605, 405, 503, 205, 30),
(606, 406, 503, 206, 20),
(607, 407, 504, 207, 25),
(608, 408, 504, 208, 30);

INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status) VALUES
(701, 301, 601, '2023-08-05', 'Approved'),
(702, 302, 607, '2024-01-12', 'Approved'),
(703, 303, 602, '2023-08-10', 'Approved'),
(704, 304, 606, '2024-06-05', 'Rejected'),
(705, 305, 605, '2024-06-02', 'Approved'),
(706, 306, 603, '2024-01-15', 'Approved'),
(707, 307, 608, '2024-08-10', 'Approved'),
(708, 308, 604, '2024-01-20', 'Approved');

INSERT INTO StudentGrades (enrollmentId, grade, remarks) VALUES
(701, 85.5, 'Good performance'),
(702, 92.0, 'Excellent work'),
(703, 78.5, 'Needs improvement'),
(705, 88.5, 'Consistent effort'),
(706, 95.0, 'Top of the class'),
(707, 72.5, 'Average'),
(708, 81.0, 'Good participation');
