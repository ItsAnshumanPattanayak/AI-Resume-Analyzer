import { useRef, useState } from "react";

const ACCEPTED_FILE_TYPES = [".pdf", ".docx"];
const MAXIMUM_FILE_SIZE = 5 * 1024 * 1024;

const MODE_CONTENT = {
  analyze: {
    eyebrow: "Complete analysis",
    title: "Compare your resume with a job",
    button: "Analyze resume",
    loading: "Analyzing resume...",
  },
  parse: {
    eyebrow: "Resume parser",
    title: "Extract structured resume information",
    button: "Parse resume",
    loading: "Parsing resume...",
  },
  roles: {
    eyebrow: "Career recommendation",
    title: "Discover your best-fit job roles",
    button: "Recommend roles",
    loading: "Finding suitable roles...",
  },
  improve: {
    eyebrow: "Writing analysis",
    title: "Find ways to improve your resume",
    button: "Check resume quality",
    loading: "Checking resume quality...",
  },
};

function ResumeForm({
  mode,
  onSubmit,
  loading,
}) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [topN, setTopN] = useState(5);
  const [formError, setFormError] = useState("");
  const fileInputRef = useRef(null);
  const submissionPendingRef = useRef(false);

  const modeContent =
    MODE_CONTENT[mode] || MODE_CONTENT.analyze;

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
      setFormError(
        "Only PDF and DOCX resumes are supported.",
      );
      event.target.value = "";
      return;
    }

    if (selectedFile.size > MAXIMUM_FILE_SIZE) {
      setResumeFile(null);
      setFormError(
        "The resume must be smaller than 5 MB.",
      );
      event.target.value = "";
      return;
    }

    setResumeFile(selectedFile);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (loading || submissionPendingRef.current) {
      return;
    }

    setFormError("");

    if (!resumeFile) {
      setFormError(
        "Please select a PDF or DOCX resume.",
      );
      return;
    }

    if (
      mode === "analyze" &&
      jobDescription.trim().length < 50
    ) {
      setFormError(
        "Please enter a job description containing at least 50 characters.",
      );
      return;
    }

    submissionPendingRef.current = true;
    try {
      await onSubmit({
        resumeFile,
        jobDescription: jobDescription.trim(),
        topN,
      });
    } finally {
      submissionPendingRef.current = false;
    }
  }

  function clearForm() {
    setResumeFile(null);
    setJobDescription("");
    setTopN(5);
    setFormError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <form
      className="analyzer-form"
      onSubmit={handleSubmit}
    >
      <div className="form-heading">
        <div>
          <p className="eyebrow">
            {modeContent.eyebrow}
          </p>
          <h2>{modeContent.title}</h2>
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

      <label
        className="field-label"
        htmlFor="resume"
      >
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
            {resumeFile
              ? resumeFile.name
              : "Choose your resume"}
          </strong>

          <span>
            {resumeFile
              ? `${(
                  resumeFile.size / 1024
                ).toFixed(1)} KB`
              : "PDF or DOCX, maximum 5 MB"}
          </span>
        </div>
      </div>

      {mode === "analyze" && (
        <>
          <label
            className="field-label"
            htmlFor="job-description"
          >
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
        </>
      )}

      {mode === "roles" && (
        <>
          <label
            className="field-label"
            htmlFor="top-n"
          >
            Number of role recommendations
          </label>

          <select
            id="top-n"
            value={topN}
            onChange={(event) =>
              setTopN(Number(event.target.value))
            }
            disabled={loading}
          >
            <option value={3}>Top 3 roles</option>
            <option value={5}>Top 5 roles</option>
            <option value={7}>Top 7 roles</option>
            <option value={10}>Top 10 roles</option>
          </select>
        </>
      )}

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
        {loading
          ? modeContent.loading
          : modeContent.button}
      </button>

      <p className="privacy-note">
        The resume is processed for analysis and is not
        permanently stored by the current backend.
      </p>
    </form>
  );
}

export default ResumeForm;
