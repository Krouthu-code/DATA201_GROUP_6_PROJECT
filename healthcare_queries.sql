USE healthcare_db;
CREATE TABLE Admissions (
    admission_id      INT AUTO_INCREMENT PRIMARY KEY,
    patient_id        INT,
    doctor_id         INT,
    hospital_id       INT,
    condition_id     INT,
    medication_id  INT,
    admission_type    VARCHAR(20),
    date_of_admission DATE,
    discharge_date    DATE,
    room_number      INT,
    billing_amount    DECIMAL(10, 2),
    test_results      VARCHAR(20),
    FOREIGN KEY (patient_id)   REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id)    REFERENCES Doctors(doctor_id),
    FOREIGN KEY (hospital_id)  REFERENCES Hospitals(hospital_id),
    FOREIGN KEY (condition_id) REFERENCES Medical_Conditions(condition_id),
    FOREIGN KEY (medication_id) REFERENCES Medications(medication_id)
);


USE healthcare_db;
INSERT INTO Admissions (
    patient_id, doctor_id, hospital_id, condition_id, medication_id,
    admission_type, date_of_admission, discharge_date,
    room_number, billing_amount, test_results
)
SELECT
    p.patient_id,
    d.doctor_id,
    h.hospital_id,
    mc.condition_id,
    m.medication_id,
    r.raw_admit_type,
    r.raw_admit_date,
    r.raw_discharge_date,
    r.raw_room,
    r.raw_billing,
    r.raw_test_results
FROM raw_healthcare r
JOIN Patients            p  ON TRIM(r.raw_name)      = p.full_name
JOIN Hospitals           h  ON TRIM(r.raw_hospital)  = h.hospital_name
JOIN Doctors             d  ON TRIM(r.raw_doctor)    = d.doctor_name AND d.hospital_id = h.hospital_id
JOIN Medical_Conditions  mc ON TRIM(r.raw_condition) = mc.condition_name
JOIN Medications         m  ON TRIM(r.raw_medication) = m.medication_name;
