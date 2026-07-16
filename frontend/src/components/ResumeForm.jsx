import { useRef, useState } from "react";

const ACCEPTED_FILE_TYPES = [".pdf", ".docx"];
const MAXIMUM_FILE_SIZE = 5 * 1024 * 1024;

function ResumeForm({ onAnalyze, loading }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [formError, setFormError] = useState("");
  const fileInputRef = useRef(null);

  function handleFileChange(event) {
    setFormError("");

    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      setResumeFile(null);
      return;
    }

    const extension = selectedFile.name
      .slice(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (!ACCEPTED_FILE_TYPES.includes(extension)) {
      setResumeFile(null);
      setFormError("Only PDF and DOCX resumes are supported.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size > MAXIMUM_FILE_SIZE) {
      setResumeFile(null);
      setFormError("The resume must be smaller than 5 MB.");
      event.target.value = "";
      return;
    }

    setResumeFile(selectedFile);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    if (!resumeFile) {
      setFormError("Please select a PDF or DOCX resume.");
      return;
    }

    if (jobDescription.trim().length < 50) {
      setFormError(
        "Please enter a job description containing at least 50 characters.",
      );
      return;
    }

    await onAnalyze(resumeFile, jobDescription.trim());
  }

  function clearForm() {
    setResumeFile(null);
    setJobDescription("");
    setFormError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <form className="analyzer-form" onSubmit={handleSubmit}>
      <div className="form-heading">
        <div>
          <p className="eyebrow">Resume analysis</p>
          <h2>Compare your resume with a job</h2>
        </div>

        <button
          className="text-button"
          type="button"
          onClick={clearForm}
          disabled={loading}
        >
          Clear
        </button>
      </div>

      <label className="field-label" htmlFor="resume">
        Resume
      </label>

      <div className="file-upload">
        <input
          ref={fileInputRef}
          id="resume"
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileChange}
          disabled={loading}
        />

        <div>
          <strong>
            {resumeFile ? resumeFile.name : "Choose your resume"}
          </strong>

          <span>
            {resumeFile
              ? `${(resumeFile.size / 1024).toFixed(1)} KB`
              : "PDF or DOCX, maximum 5 MB"}
          </span>
        </div>
      </div>

      <label className="field-label" htmlFor="job-description">
        Job description
      </label>

      <textarea
        id="job-description"
        value={jobDescription}
        onChange={(event) =>
          setJobDescription(event.target.value)
        }
        placeholder="Paste the complete job description here..."
        rows={12}
        disabled={loading}
      />

      <div className="character-counter">
        {jobDescription.trim().length} characters
      </div>

      {formError && (
        <div className="form-error" role="alert">
          {formError}
        </div>
      )}

      <button
        className="primary-button"
        type="submit"
        disabled={loading}
      >
        {loading ? "Analyzing resume..." : "Analyze resume"}
      </button>

      <p className="privacy-note">
        Your uploaded file is processed for analysis and is not
        permanently stored by the current backend.
      </p>
    </form>
  );
}

export default ResumeForm;