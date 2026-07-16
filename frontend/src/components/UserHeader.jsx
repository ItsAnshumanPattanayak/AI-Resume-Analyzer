import { useAuth } from "../context/useAuth";


function UserHeader() {
  const {
    user,
    logout,
  } = useAuth();

  return (
    <header className="site-header">
      <a className="brand" href="/">
        <span className="brand-mark">
          RA
        </span>

        <div>
          <strong>
            Resume Analyzer
          </strong>

          <small>
            AI-powered career analysis
          </small>
        </div>
      </a>

      <div className="user-header-actions">
        <div className="user-summary">
          <strong>{user?.name}</strong>
          <span>{user?.email}</span>
        </div>

        <button
          className="secondary-button"
          type="button"
          onClick={logout}
        >
          Logout
        </button>
      </div>
    </header>
  );
}


export default UserHeader;