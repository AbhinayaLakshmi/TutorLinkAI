import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { API_BASE_URL } from "../services/api";
import { logout } from "../services/auth";
import "../onboarding.css";

export default function ReviewerDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [queue, setQueue] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingQueue, setLoadingQueue] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Modal / Decision state
  const [decisionModal, setDecisionModal] = useState(null); // "APPROVED" | "REJECTED" | "RESUBMISSION_REQUESTED" | null
  const [decisionReason, setDecisionReason] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [modalError, setModalError] = useState("");

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    fetchQueue();
  }, []);

  const fetchQueue = async () => {
    setLoadingQueue(true);
    setError("");
    try {
      const res = await api.get("/api/verification/reviewer/manual-reviews");
      setQueue(res.data);
      if (res.data.length > 0) {
        if (!selectedId || !res.data.some((item) => item.id === selectedId)) {
          fetchDetail(res.data[0].id);
        }
      } else {
        setSelectedId(null);
        setDetail(null);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load manual review queue.");
    } finally {
      setLoadingQueue(false);
    }
  };

  const fetchDetail = async (id) => {
    setSelectedId(id);
    setLoadingDetail(true);
    setSuccess("");
    setError("");
    try {
      const res = await api.get(`/api/verification/reviewer/manual-reviews/${id}`);
      setDetail(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load review evidence details.");
      setDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleOpenDecisionModal = (decisionType) => {
    setDecisionModal(decisionType);
    setDecisionReason("");
    setModalError("");
  };

  const handleCloseDecisionModal = () => {
    setDecisionModal(null);
    setDecisionReason("");
    setModalError("");
  };

  const handleSubmitDecision = async () => {
    if (!decisionModal || !selectedId) return;

    if (
      (decisionModal === "REJECTED" || decisionModal === "RESUBMISSION_REQUESTED") &&
      !decisionReason.trim()
    ) {
      setModalError(`A clear reason is required for ${decisionModal.replace("_", " ")}.`);
      return;
    }

    setSubmittingDecision(true);
    setModalError("");

    try {
      await api.post(`/api/verification/reviewer/manual-reviews/${selectedId}/decision`, {
        decision: decisionModal,
        reason: decisionReason.trim() || null,
      });

      setSuccess(`Review decision (${decisionModal.replace("_", " ")}) submitted successfully!`);
      handleCloseDecisionModal();
      
      // Refresh queue
      const updatedQueueRes = await api.get("/api/verification/reviewer/manual-reviews");
      setQueue(updatedQueueRes.data);
      if (updatedQueueRes.data.length > 0) {
        fetchDetail(updatedQueueRes.data[0].id);
      } else {
        setSelectedId(null);
        setDetail(null);
      }
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to submit decision. Please try again.");
    } finally {
      setSubmittingDecision(false);
    }
  };

  const handleDownloadCertificate = async (certificateId, filename) => {
    try {
      const response = await api.get(
        `/api/verification/reviewer/certificates/${certificateId}/download`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename || "certificate");
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Failed to download certificate file.");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-color)", color: "var(--text-color)" }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          borderBottom: "1px solid var(--border-color)",
          backgroundColor: "var(--card-bg)",
          padding: "16px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h1 style={{ fontSize: "20px", fontWeight: "700", margin: 0, color: "var(--primary-color)" }}>
            TutorLinkAI
          </h1>
          <span
            style={{
              fontSize: "12px",
              padding: "2px 8px",
              borderRadius: "4px",
              backgroundColor: "rgba(59, 130, 246, 0.15)",
              color: "var(--primary-color)",
              fontWeight: "600",
            }}
          >
            Reviewer Portal
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontWeight: "600", fontSize: "14px" }}>{user?.full_name || "Verification Reviewer"}</div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{user?.email}</div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "1px solid var(--border-color)",
              backgroundColor: "transparent",
              color: "var(--text-color)",
              cursor: "pointer",
              fontSize: "13px",
              fontWeight: "500",
            }}
          >
            Log Out
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div style={{ padding: "24px 32px", maxWidth: "1500px", margin: "0 auto" }}>
        {error && (
          <div className="alert alert-error" style={{ marginBottom: "20px" }}>
            {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success" style={{ marginBottom: "20px" }}>
            {success}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "24px", alignItems: "start" }}>
          {/* Left Column: Manual Review Queue */}
          <div
            style={{
              backgroundColor: "var(--card-bg)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.02)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "16px", fontWeight: "700", margin: 0 }}>
                Pending Reviews ({queue.length})
              </h2>
              <button
                onClick={fetchQueue}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--primary-color)",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: "600",
                }}
              >
                Refresh
              </button>
            </div>

            {loadingQueue ? (
              <p style={{ fontSize: "14px", color: "var(--text-muted)", textAlign: "center", padding: "20px 0" }}>
                Loading review queue...
              </p>
            ) : queue.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px 16px", color: "var(--text-muted)" }}>
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>✓</div>
                <div style={{ fontWeight: "600", fontSize: "14px" }}>Queue is empty</div>
                <div style={{ fontSize: "12px", marginTop: "4px" }}>No verification records currently require manual review.</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {queue.map((item) => {
                  const isSelected = item.id === selectedId;
                  return (
                    <div
                      key={item.id}
                      onClick={() => fetchDetail(item.id)}
                      style={{
                        padding: "14px",
                        borderRadius: "6px",
                        border: isSelected ? "2px solid var(--primary-color)" : "1px solid var(--border-color)",
                        backgroundColor: isSelected ? "rgba(59, 130, 246, 0.05)" : "transparent",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "4px" }}>
                        <span style={{ fontWeight: "600", fontSize: "14px" }}>{item.tutor_name}</span>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: "#fef3c7",
                            color: "#92400e",
                          }}
                        >
                          MANUAL REVIEW
                        </span>
                      </div>
                      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "6px" }}>
                        {item.tutor_email}
                      </div>
                      <div style={{ fontSize: "12px", color: "var(--text-color)", marginBottom: "4px" }}>
                        📄 {item.certificate_filename}
                      </div>
                      {item.failure_reason && (
                        <div
                          style={{
                            fontSize: "11px",
                            color: "#b45309",
                            backgroundColor: "rgba(245, 158, 11, 0.1)",
                            padding: "4px 8px",
                            borderRadius: "4px",
                            marginTop: "6px",
                          }}
                        >
                          Trigger: {item.failure_reason}
                        </div>
                      )}
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "8px" }}>
                        Updated: {new Date(item.updated_at).toLocaleString()}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Review Evidence & Decision Panel */}
          <div
            style={{
              backgroundColor: "var(--card-bg)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "24px",
              boxShadow: "0 2px 4px rgba(0,0,0,0.02)",
            }}
          >
            {loadingDetail ? (
              <p style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)" }}>
                Loading evidence summary...
              </p>
            ) : !detail ? (
              <div style={{ textAlign: "center", padding: "80px 20px", color: "var(--text-muted)" }}>
                <div style={{ fontSize: "36px", marginBottom: "12px" }}>🔍</div>
                <h3 style={{ margin: "0 0 8px 0" }}>Select a verification record</h3>
                <p style={{ margin: 0, fontSize: "14px" }}>
                  Choose a pending case from the queue on the left to inspect multi-modal evidence.
                </p>
              </div>
            ) : (
              <div>
                {/* Header & Quick Decision Controls */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingBottom: "20px",
                    borderBottom: "1px solid var(--border-color)",
                    marginBottom: "24px",
                    flexWrap: "wrap",
                    gap: "16px",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <h2 style={{ fontSize: "20px", fontWeight: "700", margin: 0 }}>
                        {detail.tutor.full_name}
                      </h2>
                      <span
                        style={{
                          fontSize: "12px",
                          fontWeight: "600",
                          padding: "3px 8px",
                          borderRadius: "4px",
                          backgroundColor: "#fef3c7",
                          color: "#92400e",
                        }}
                      >
                        MANUAL REVIEW REQUIRED
                      </span>
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                      Record ID: {detail.verification_record.id} • Tutor ID: {detail.tutor.id}
                    </div>
                  </div>

                  {/* Decision Action Buttons */}
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      onClick={() => handleOpenDecisionModal("APPROVED")}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#10b981",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        fontWeight: "600",
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                    >
                      ✓ Approve Tutor
                    </button>
                    <button
                      onClick={() => handleOpenDecisionModal("RESUBMISSION_REQUESTED")}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#f59e0b",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        fontWeight: "600",
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                    >
                      ↺ Request Resubmission
                    </button>
                    <button
                      onClick={() => handleOpenDecisionModal("REJECTED")}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#ef4444",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        fontWeight: "600",
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>

                {/* Evidence Sections Grid */}
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  {/* Section 1: Tutor Profile & Declared Education */}
                  <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                    <h3 style={{ fontSize: "15px", fontWeight: "700", margin: "0 0 14px 0", color: "var(--primary-color)" }}>
                      1. Declared Tutor Profile & Education
                    </h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px", marginBottom: "16px" }}>
                      <div><strong>Full Name:</strong> {detail.tutor.full_name}</div>
                      <div><strong>Email:</strong> {detail.tutor.email}</div>
                      <div><strong>Phone:</strong> {detail.tutor.phone_number || "Not provided"}</div>
                      <div><strong>Location:</strong> {detail.tutor.location || "Not specified"}</div>
                      <div><strong>Teaching Mode:</strong> {detail.tutor.preferred_teaching_mode || "Not specified"}</div>
                      <div><strong>Languages:</strong> {detail.tutor.languages_spoken?.join(", ") || "None"}</div>
                    </div>

                    <h4 style={{ fontSize: "13px", fontWeight: "600", margin: "0 0 8px 0" }}>Declared Qualifications:</h4>
                    {detail.tutor.education?.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                        {detail.tutor.education.map((edu, idx) => (
                          <div
                            key={idx}
                            style={{
                              padding: "10px",
                              backgroundColor: "rgba(0,0,0,0.02)",
                              border: "1px solid var(--border-color)",
                              borderRadius: "6px",
                              fontSize: "13px",
                            }}
                          >
                            <div><strong>Degree:</strong> {edu.degree_name} ({edu.highest_degree})</div>
                            <div><strong>University / Institution:</strong> {edu.university}</div>
                            <div><strong>Graduation Year:</strong> {edu.graduation_year}</div>
                            {edu.specialization && <div><strong>Specialization:</strong> {edu.specialization}</div>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>No education records declared.</div>
                    )}
                  </div>

                  {/* Section 2: Uploaded Certificate */}
                  <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                      <h3 style={{ fontSize: "15px", fontWeight: "700", margin: 0, color: "var(--primary-color)" }}>
                        2. Certificate Document
                      </h3>
                      {detail.certificate.id && (
                        <button
                          onClick={() =>
                            handleDownloadCertificate(detail.certificate.id, detail.certificate.original_filename)
                          }
                          style={{
                            padding: "6px 12px",
                            backgroundColor: "var(--card-bg)",
                            border: "1px solid var(--primary-color)",
                            color: "var(--primary-color)",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontWeight: "600",
                            cursor: "pointer",
                          }}
                        >
                          ⬇ Secure Download
                        </button>
                      )}
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "13px" }}>
                      <div><strong>Filename:</strong> {detail.certificate.original_filename}</div>
                      <div><strong>Type:</strong> {detail.certificate.file_type}</div>
                      <div><strong>Size:</strong> {(detail.certificate.file_size / 1024).toFixed(1)} KB</div>
                      <div>
                        <strong>Uploaded At:</strong>{" "}
                        {detail.certificate.upload_timestamp
                          ? new Date(detail.certificate.upload_timestamp).toLocaleString()
                          : "N/A"}
                      </div>
                    </div>
                  </div>

                  {/* Section 3 & 4: OCR Extraction & Profile-Certificate Consistency */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                    {/* OCR Extraction */}
                    <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                        <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>3. OCR Extraction</h3>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor: detail.verification_record.ocr_status === "COMPLETED" ? "#d1fae5" : "#fee2e2",
                            color: detail.verification_record.ocr_status === "COMPLETED" ? "#065f46" : "#991b1b",
                          }}
                        >
                          {detail.verification_record.ocr_status}
                        </span>
                      </div>

                      {detail.verification_record.ocr_metadata ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px" }}>
                          <div><strong>Extracted Name:</strong> {detail.verification_record.ocr_metadata.name || "None"}</div>
                          <div><strong>Extracted University:</strong> {detail.verification_record.ocr_metadata.university || "None"}</div>
                          <div><strong>Extracted Degree:</strong> {detail.verification_record.ocr_metadata.degree || "None"}</div>
                          <div><strong>Graduation Year:</strong> {detail.verification_record.ocr_metadata.graduation_year || "None"}</div>
                          <div><strong>OCR Confidence:</strong> {detail.verification_record.ocr_metadata.confidence_level || "NORMAL"}</div>
                        </div>
                      ) : (
                        <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>No OCR metadata extracted.</div>
                      )}
                    </div>

                    {/* Consistency Matching */}
                    <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                        <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>4. Consistency Match</h3>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor:
                              detail.verification_record.certificate_validation_status === "MATCH"
                                ? "#d1fae5"
                                : detail.verification_record.certificate_validation_status === "PARTIAL_MATCH"
                                ? "#fef3c7"
                                : "#fee2e2",
                            color:
                              detail.verification_record.certificate_validation_status === "MATCH"
                                ? "#065f46"
                                : detail.verification_record.certificate_validation_status === "PARTIAL_MATCH"
                                ? "#92400e"
                                : "#991b1b",
                          }}
                        >
                          {detail.verification_record.certificate_validation_status}
                        </span>
                      </div>

                      <div style={{ fontSize: "13px", lineHeight: "1.5" }}>
                        <p style={{ margin: "0 0 8px 0" }}>
                          Automated comparison between declared tutor information and certificate OCR tokens.
                        </p>
                        {detail.verification_record.failure_reason && (
                          <div
                            style={{
                              padding: "8px",
                              backgroundColor: "rgba(239, 68, 68, 0.08)",
                              border: "1px solid rgba(239, 68, 68, 0.2)",
                              borderRadius: "4px",
                              color: "#b91c1c",
                              fontSize: "12px",
                            }}
                          >
                            <strong>Trigger / Note:</strong> {detail.verification_record.failure_reason}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Section 5 & 6: Document Security & Biometrics */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                    {/* Document Security */}
                    <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                        <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>5. Document Security</h3>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor:
                              detail.verification_record.security_analysis_status === "PASS"
                                ? "#d1fae5"
                                : detail.verification_record.security_analysis_status === "SUSPICIOUS"
                                ? "#fef3c7"
                                : "#fee2e2",
                            color:
                              detail.verification_record.security_analysis_status === "PASS"
                                ? "#065f46"
                                : detail.verification_record.security_analysis_status === "SUSPICIOUS"
                                ? "#92400e"
                                : "#991b1b",
                          }}
                        >
                          {detail.verification_record.security_analysis_status}
                        </span>
                      </div>

                      {detail.verification_record.security_analysis_metadata ? (
                        <div style={{ fontSize: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
                          <div>
                            <strong>Risk Level:</strong> {detail.verification_record.security_analysis_metadata.risk_level || "LOW"}
                          </div>
                          <div>
                            <strong>Identifiers Found:</strong>{" "}
                            {detail.verification_record.security_analysis_metadata.identifiers?.length > 0
                              ? detail.verification_record.security_analysis_metadata.identifiers.join(", ")
                              : "None"}
                          </div>
                          {detail.verification_record.security_analysis_metadata.risk_flags?.length > 0 && (
                            <div style={{ color: "#b91c1c", marginTop: "4px" }}>
                              <strong>Flags:</strong>{" "}
                              {detail.verification_record.security_analysis_metadata.risk_flags.join("; ")}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                          No document security metadata recorded.
                        </div>
                      )}
                    </div>

                    {/* Biometrics & Identity */}
                    <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                        <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>6. Biometrics & Face Modality</h3>
                        <span
                          style={{
                            fontSize: "11px",
                            fontWeight: "600",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            backgroundColor:
                              detail.verification_record.liveness_status === "PASSED" ? "#d1fae5" : "#f3f4f6",
                            color:
                              detail.verification_record.liveness_status === "PASSED" ? "#065f46" : "#4b5563",
                          }}
                        >
                          {detail.verification_record.liveness_status}
                        </span>
                      </div>

                      <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "8px" }}>
                        <div><strong>Face Quality Status:</strong> {detail.verification_record.face_verification_status}</div>
                        <div><strong>Live Liveness:</strong> {detail.verification_record.liveness_status}</div>
                        
                        {detail.verification_record.face_verification_status === "NOT_AVAILABLE" && (
                          <div
                            style={{
                              padding: "8px",
                              backgroundColor: "rgba(59, 130, 246, 0.08)",
                              borderRadius: "4px",
                              fontSize: "12px",
                              color: "#1e40af",
                            }}
                          >
                            ℹ️ <strong>No portrait photo detected on certificate</strong>. Identity similarity is marked as unavailable. You may evaluate the credential on document & OCR merits.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Section 7: Audit History */}
                  <div style={{ border: "1px solid var(--border-color)", borderRadius: "8px", padding: "18px" }}>
                    <h3 style={{ fontSize: "15px", fontWeight: "700", margin: "0 0 14px 0" }}>
                      7. Review Audit History ({detail.review_history?.length || 0})
                    </h3>

                    {detail.review_history && detail.review_history.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {detail.review_history.map((rev) => (
                          <div
                            key={rev.id}
                            style={{
                              padding: "12px",
                              backgroundColor: "rgba(0,0,0,0.02)",
                              border: "1px solid var(--border-color)",
                              borderRadius: "6px",
                              fontSize: "13px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                              <strong>Reviewer: {rev.reviewer_name || rev.reviewer_id}</strong>
                              <span
                                style={{
                                  fontWeight: "600",
                                  color:
                                    rev.decision === "APPROVED"
                                      ? "#10b981"
                                      : rev.decision === "RESUBMISSION_REQUESTED"
                                      ? "#f59e0b"
                                      : "#ef4444",
                                }}
                              >
                                {rev.decision}
                              </span>
                            </div>
                            {rev.reason && (
                              <div style={{ color: "var(--text-color)", marginTop: "4px" }}>
                                <strong>Reason:</strong> {rev.reason}
                              </div>
                            )}
                            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px" }}>
                              {new Date(rev.created_at).toLocaleString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                        No previous review actions recorded for this verification record.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Decision Modal */}
      {decisionModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              backgroundColor: "var(--card-bg)",
              border: "1px solid var(--border-color)",
              borderRadius: "8px",
              padding: "28px",
              maxWidth: "500px",
              width: "100%",
              boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
            }}
          >
            <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", fontWeight: "700" }}>
              {decisionModal === "APPROVED"
                ? "Approve Tutor Credentials"
                : decisionModal === "RESUBMISSION_REQUESTED"
                ? "Request Document Resubmission"
                : "Reject Tutor Verification"}
            </h3>

            <p style={{ margin: "0 0 16px 0", fontSize: "13px", color: "var(--text-muted)" }}>
              {decisionModal === "APPROVED"
                ? "This will promote the tutor profile and verification record to VERIFIED, granting teaching authority."
                : decisionModal === "RESUBMISSION_REQUESTED"
                ? "This will reset the verification to PENDING so the tutor can re-upload a clear certificate or correct details."
                : "This will mark the verification record and tutor profile as FAILED."}
            </p>

            {modalError && (
              <div className="alert alert-error" style={{ marginBottom: "16px", fontSize: "13px" }}>
                {modalError}
              </div>
            )}

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>
                {decisionModal === "APPROVED" ? "Audit Note (Optional):" : "Reason / Feedback (Required):"}
              </label>
              <textarea
                rows={4}
                value={decisionReason}
                onChange={(e) => setDecisionReason(e.target.value)}
                placeholder={
                  decisionModal === "APPROVED"
                    ? "e.g., Degree matches official registry and security inspection passed."
                    : decisionModal === "RESUBMISSION_REQUESTED"
                    ? "e.g., Certificate image was blurred. Please re-upload a high-resolution color scan."
                    : "e.g., Name on certificate does not match registered candidate."
                }
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "6px",
                  border: "1px solid var(--border-color)",
                  backgroundColor: "transparent",
                  color: "var(--text-color)",
                  fontSize: "13px",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
              <button
                type="button"
                onClick={handleCloseDecisionModal}
                disabled={submittingDecision}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid var(--border-color)",
                  backgroundColor: "transparent",
                  color: "var(--text-color)",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitDecision}
                disabled={submittingDecision}
                style={{
                  padding: "8px 18px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor:
                    decisionModal === "APPROVED"
                      ? "#10b981"
                      : decisionModal === "RESUBMISSION_REQUESTED"
                      ? "#f59e0b"
                      : "#ef4444",
                  color: "#ffffff",
                  fontWeight: "600",
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                {submittingDecision ? "Submitting..." : "Confirm Decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
