import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

export const TOKEN_STORAGE_KEY =
  "resume_analyzer_access_token";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});


apiClient.interceptors.request.use(
  (config) => {
    const token = window.localStorage.getItem(
      TOKEN_STORAGE_KEY,
    );

    if (token) {
      config.headers.Authorization =
        `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);


function createApiError(error) {
  return new Error(
    getApiErrorMessage(error),
    {
      cause: error,
    },
  );
}


export async function registerUser({
  name,
  email,
  password,
}) {
  try {
    const response = await apiClient.post(
      "/api/auth/register",
      {
        name,
        email,
        password,
      },
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function loginUser({
  email,
  password,
}) {
  try {
    const response = await apiClient.post(
      "/api/auth/login",
      {
        email,
        password,
      },
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function getCurrentUser() {
  try {
    const response = await apiClient.get(
      "/api/auth/me",
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function analyzeResume(
  resumeFile,
  jobDescription,
) {
  const formData = new FormData();

  formData.append("file", resumeFile);
  formData.append(
    "job_description",
    jobDescription,
  );

  try {
    const response = await apiClient.post(
      "/api/resume/analyze",
      formData,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function parseResume(
  resumeFile,
) {
  const formData = new FormData();

  formData.append("file", resumeFile);

  try {
    const response = await apiClient.post(
      "/api/resume/parse",
      formData,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function improveResume(
  resumeFile,
) {
  const formData = new FormData();

  formData.append("file", resumeFile);

  try {
    const response = await apiClient.post(
      "/api/resume/improve",
      formData,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function recommendRoles(
  resumeFile,
  topN = 5,
) {
  const formData = new FormData();

  formData.append("file", resumeFile);
  formData.append(
    "top_n",
    String(topN),
  );

  try {
    const response = await apiClient.post(
      "/api/resume/recommend-roles",
      formData,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function getAnalysisHistory(
  limit = 20,
  offset = 0,
) {
  try {
    const response = await apiClient.get(
      "/api/history",
      {
        params: {
          limit,
          offset,
        },
      },
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function getAnalysisHistoryDetail(
  recordId,
) {
  try {
    const response = await apiClient.get(
      `/api/history/${recordId}`,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


export async function deleteAnalysisHistory(
  recordId,
) {
  try {
    const response = await apiClient.delete(
      `/api/history/${recordId}`,
    );

    return response.data;
  } catch (error) {
    throw createApiError(error);
  }
}


function getApiErrorMessage(error) {
  if (!error.response) {
    if (error.code === "ECONNABORTED") {
      return (
        "The request took too long. " +
        "Please try again."
      );
    }

    return (
      "The browser could not read the backend response. " +
      "Check that FastAPI is running and that the frontend " +
      "origin is allowed by the backend CORS configuration."
    );
  }

  const responseData =
    error.response.data;

  if (responseData?.error?.message) {
    const message =
      responseData.error.message;

    if (typeof message === "string") {
      return message;
    }

    if (message?.message) {
      return message.message;
    }

    return JSON.stringify(message);
  }

  if (responseData?.detail) {
    if (
      typeof responseData.detail ===
      "string"
    ) {
      return responseData.detail;
    }

    if (
      responseData.detail?.message
    ) {
      return responseData.detail.message;
    }

    return JSON.stringify(
      responseData.detail,
    );
  }

  if (
    typeof responseData?.message ===
    "string"
  ) {
    return responseData.message;
  }

  return (
    `Request failed with status ` +
    `${error.response.status}.`
  );
}


export default apiClient;