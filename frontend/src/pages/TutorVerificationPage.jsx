import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import "../onboarding.css";

export default function TutorVerificationPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [tutorProfile, setTutorProfile] = useState(null);
  const [verificationRecord, setVerificationRecord] = useState(null);

  const fetchStatus = async () => {
    try {
      // 1. Get tutor profile (to verify certificate is uploaded)
      const profileRes = await api.get("/api/onboarding/tutor/me");
      setTutorProfile(profileRes.data);

      // 2. Get detailed verification record if exists
      try {
        const recordRes = await api.get("/api/verification/tutor/me");
        setVerificationRecord(recordRes.data);
      } catch (err) {
        if (err.response?.status === 404) {
          // No record exists yet, that's fine
          setVerificationRecord(null);
        } else {
          throw err;
        }
      }
    } catch (err) {
      setError("Failed to load verification status. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleStartVerification = async () => {
    setError("");
    setSuccess("");
    setProcessing(true);

    try {
      const res = await api.post("/api/verification/tutor/me/start");
      setVerificationRecord(res.data);
      setSuccess("Verification process initiated successfully!");
      setTimeout(() => setSuccess(""), 3000);
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start verification pipeline.");
    } finally {
      setProcessing(false);
    }
  };

  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [livenessStep, setLivenessStep] = useState(0); // 0: idle, 1: straight, 2: action, 3: processing
  const [targetAction, setTargetAction] = useState(""); // "HEAD_LEFT" or "HEAD_RIGHT"
  const [frameStraight, setFrameStraight] = useState("");
  const [frameAction, setFrameAction] = useState("");
  const [livenessResult, setLivenessResult] = useState(null);

  const videoRef = React.useRef(null);
  const streamRef = React.useRef(null);

  const startCamera = async () => {
    setCameraError("");
    setError("");
    setLivenessResult(null);

    // Stop any existing stream first to avoid leaks
    if (streamRef.current) {
      console.log("Stopping existing camera stream...");
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    try {
      console.log("Requesting camera permissions via getUserMedia...");
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      console.log("Camera access granted. Stream:", stream);

      const tracks = stream.getTracks();
      console.log("Camera tracks:", tracks);
      tracks.forEach((track, index) => {
        console.log(`Track [${index}] info:`, {
          label: track.label,
          readyState: track.readyState,
          enabled: track.enabled
        });
      });

      streamRef.current = stream;
      setCameraActive(true);
      setLivenessStep(1);
    } catch (err) {
      console.error("Camera access failed:", err);
      setCameraError("Camera access denied or unavailable. Please enable camera permissions.");
      setLivenessStep(0);
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      console.log("Stopping active camera stream...");
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    if (cameraActive && streamRef.current && videoRef.current) {
      console.log("Binding stream to video element via useEffect ref hook...");
      videoRef.current.srcObject = streamRef.current;
      
      videoRef.current.onloadedmetadata = () => {
        console.log("Video track metadata loaded. Dimensions:", {
          videoWidth: videoRef.current.videoWidth,
          videoHeight: videoRef.current.videoHeight
        });
      };

      videoRef.current.play()
        .then(() => console.log("Camera stream play started successfully."))
        .catch(playErr => console.error("Failed to start video playback:", playErr));
    }
  }, [cameraActive, livenessStep]);

  const captureFrame = () => {
    if (!videoRef.current) return null;
    const canvas = document.createElement("canvas");
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg");
  };

  const handleCaptureStraight = () => {
    const frame = captureFrame();
    if (frame) {
      setFrameStraight(frame);
      const action = Math.random() > 0.5 ? "LEFT" : "RIGHT";
      setTargetAction(action);
      setLivenessStep(2);
    }
  };

  const handleCaptureAction = async () => {
    const frame = captureFrame();
    if (frame) {
      setFrameAction(frame);
      setLivenessStep(3);
      stopCamera();
      
      try {
        setError("");
        const payload = {
          action: targetAction,
          frame_straight: frameStraight,
          frame_action: frame
        };
        console.log("Sending liveness payload:", {
          action: payload.action,
          frame_straight_length: payload.frame_straight?.length,
          frame_action_length: payload.frame_action?.length
        });
        const res = await api.post("/api/verification/tutor/me/live-face", payload);
        console.log("Liveness response received:", res.data);
        setLivenessResult(res.data);
        if (res.data.liveness_status === "FAILED") {
          setError(res.data.reason || "Liveness verification failed.");
        }
        fetchStatus();
      } catch (err) {
        console.error("Liveness request error:", err);
        setError(err.response?.data?.detail || "Liveness verification failed. Please try again.");
        setLivenessStep(0);
      }
    }
  };

  const handleLivenessRetry = () => {
    setLivenessResult(null);
    setFrameStraight("");
    setFrameAction("");
    setLivenessStep(0);
    startCamera();
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="onboard-container">
        <div className="onboard-card" style={{ textAlign: "center" }}>
          <p>Loading verification records...</p>
        </div>
      </div>
    );
  }

  const hasCertificate = tutorProfile?.certificates && tutorProfile.certificates.length > 0;
  const latestCert = hasCertificate ? tutorProfile.certificates[tutorProfile.certificates.length - 1] : null;

  // Determine pipeline step states
  const ocrState = verificationRecord?.ocr_status || "PENDING";
  const validationState = verificationRecord?.certificate_validation_status || "PENDING";
  const securityState = verificationRecord?.security_analysis_status || "PENDING";
  const overallState = verificationRecord?.verification_status || tutorProfile?.verification_status || "PENDING";
  const securityMetadata = verificationRecord?.security_analysis_metadata;

  return (
    <div className="onboard-container">
      <div className="onboard-card" style={{ maxWidth: "650px" }}>
        <h2 className="onboard-title">Tutor Vetting & Verification</h2>
        <p className="onboard-subtitle">Phase 1: Automated Credential OCR & Consistency Matching</p>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Overview Status Panel */}
        <div 
          className="review-section" 
          style={{ 
            background: "rgba(255,255,255,0.05)", 
            border: "1px solid var(--border-color)", 
            padding: "20px", 
            borderRadius: "8px", 
            marginBottom: "30px" 
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 style={{ margin: 0, fontSize: "16px" }}>Overall Status</h3>
              <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--text-muted)" }}>
                Current evaluation result of your credentials
              </p>
            </div>
            <span 
              className="chip" 
              style={{ 
                margin: 0, 
                padding: "6px 14px", 
                fontSize: "13px",
                fontWeight: "600",
                backgroundColor: 
                  overallState === "VERIFIED" ? "#d1fae5" :
                  overallState === "FAILED" ? "#fee2e2" :
                  overallState === "MANUAL_REVIEW" ? "#fef3c7" : "#eff6ff",
                color: 
                  overallState === "VERIFIED" ? "#065f46" :
                  overallState === "FAILED" ? "#991b1b" :
                  overallState === "MANUAL_REVIEW" ? "#92400e" : "#1e40af",
              }}
            >
              {overallState.replace("_", " ")}
            </span>
          </div>

          {overallState === "PENDING" && (
            <div style={{ marginTop: "15px", fontSize: "13px", color: "var(--text-muted)", borderTop: "1px solid var(--border-color)", paddingTop: "15px" }}>
              ℹ️ Your certificate consistency check has passed successfully. Your profile remains in <strong>PENDING</strong> status until secondary verification steps (e.g. institution verification and face matching) are finalized in future phases.
            </div>
          )}

          {overallState === "MANUAL_REVIEW" && (
            <div style={{ marginTop: "15px", fontSize: "13px", color: "var(--text-muted)", borderTop: "1px solid var(--border-color)", paddingTop: "15px" }}>
              ⚠️ Fuzzy comparisons detected minor discrepancies or OCR confidence was low. A human administrator is currently auditing your credentials. No action is required.
            </div>
          )}

          {overallState === "FAILED" && (
            <div style={{ marginTop: "15px", fontSize: "13px", color: "var(--error-color)", borderTop: "1px solid var(--border-color)", paddingTop: "15px" }}>
              ❌ <strong>Verification Failed</strong>: {verificationRecord?.failure_reason || "Information discrepancy detected."} Please verify your profile details match your degree name, or upload a new certificate.
            </div>
          )}
        </div>

        {/* Verification Pipeline List */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", marginBottom: "35px" }}>
          
          {/* Step 1: Certificate Uploaded */}
          <div style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}>
            <div className="step-item completed" style={{ flexShrink: 0, width: "30px", height: "30px", fontSize: "14px" }}>
              {hasCertificate ? "✓" : "!"}
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "600" }}>Degree Certificate Upload</h4>
              <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                {hasCertificate ? `Uploaded file: ${latestCert.original_filename}` : "No certificate uploaded yet."}
              </p>
            </div>
          </div>

          {/* Step 2: OCR Extraction */}
          <div style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}>
            <div 
              className={`step-item ${ocrState === "COMPLETED" ? "completed" : ocrState === "PROCESSING" ? "active" : ""}`} 
              style={{ flexShrink: 0, width: "30px", height: "30px", fontSize: "14px" }}
            >
              {ocrState === "COMPLETED" ? "✓" : ocrState === "PROCESSING" ? "⚙" : "2"}
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "600" }}>OCR Text Extraction</h4>
              <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                PaddleOCR text processing: {ocrState}
              </p>
            </div>
          </div>

          {/* Step 3: Consistency Validation */}
          <div style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}>
            <div 
              className={`step-item ${
                validationState === "MATCH" ? "completed" : 
                validationState === "PENDING" ? "" : "active"
              }`} 
              style={{ 
                flexShrink: 0, 
                width: "30px", 
                height: "30px", 
                fontSize: "14px",
                backgroundColor: 
                  validationState === "MISMATCH" ? "var(--error-color)" : 
                  validationState === "PARTIAL_MATCH" ? "#d97706" : ""
              }}
            >
              {validationState === "MATCH" ? "✓" : validationState === "PENDING" ? "3" : "!"}
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "600" }}>Profile Consistency Match</h4>
              <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                Comparison status: {validationState.replace("_", " ")}
              </p>
            </div>
          </div>

          {/* Step 4: Security Feature Analysis */}
          <div 
            style={{ 
              display: "flex", 
              gap: "15px", 
              alignItems: "flex-start",
              opacity: securityState === "PENDING" ? "0.5" : "1"
            }}
          >
            <div 
              className={`step-item ${securityState === "PASS" ? "completed" : securityState === "PENDING" ? "" : "active"}`}
              style={{ 
                flexShrink: 0, 
                width: "30px", 
                height: "30px", 
                fontSize: "14px",
                backgroundColor: 
                  securityState === "FAIL" ? "var(--error-color)" : 
                  securityState === "SUSPICIOUS" ? "#d97706" : ""
              }}
            >
              {securityState === "PASS" ? "✓" : securityState === "PENDING" ? "4" : "!"}
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "600" }}>Security Analysis (Holograms & Seals)</h4>
              <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                Status: {securityState.replace("_", " ")}
                {securityMetadata && ` (Risk Score: ${securityMetadata.risk_score})`}
              </p>
              
              {securityMetadata?.flags && securityMetadata.flags.length > 0 && (
                <ul style={{ margin: "8px 0 0 0", paddingLeft: "20px", fontSize: "11px", color: "var(--text-muted)", display: "flex", flexDirection: "column", gap: "4px" }}>
                  {securityMetadata.flags.map((flag, idx) => (
                    <li key={idx} style={{ color: flag.severity === "CRITICAL" ? "var(--error-color)" : flag.severity === "WARNING" ? "#d97706" : "var(--text-muted)" }}>
                      <strong>[{flag.severity}]</strong> {flag.description}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {/* Step 5: Face Verification */}
          <div 
            style={{ 
              display: "flex", 
              gap: "15px", 
              alignItems: "flex-start", 
              opacity: verificationRecord ? "1" : "0.5",
              borderTop: "1px solid var(--border-color)",
              paddingTop: "20px",
              flexDirection: "column",
              width: "100%"
            }}
          >
            <div style={{ display: "flex", gap: "15px", alignItems: "flex-start" }}>
              <div 
                className={`step-item ${
                  verificationRecord?.liveness_status === "PASSED" ? "completed" : 
                  verificationRecord?.liveness_status === "PENDING" || verificationRecord?.liveness_status === "NOT_AVAILABLE" ? "" : "active"
                }`} 
                style={{ 
                  flexShrink: 0, 
                  width: "30px", 
                  height: "30px", 
                  fontSize: "14px",
                  backgroundColor: 
                    verificationRecord?.liveness_status === "FAILED" ? "var(--error-color)" : 
                    verificationRecord?.liveness_status === "MANUAL_REVIEW" ? "#d97706" : ""
                }}
              >
                {verificationRecord?.liveness_status === "PASSED" ? "✓" : "5"}
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: "14px", fontWeight: "600" }}>Biometric Face Verification & Liveness</h4>
                <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "var(--text-muted)" }}>
                  Liveness: {
                    verificationRecord?.liveness_status === "NOT_AVAILABLE" ? "NOT STARTED" :
                    (verificationRecord?.liveness_status?.replace("_", " ") || "NOT STARTED")
                  }
                </p>
              </div>
            </div>

            {verificationRecord && verificationRecord.liveness_status !== "PASSED" && (
              <div style={{ width: "100%", paddingLeft: "45px" }}>
                {livenessStep === 0 && !livenessResult && (
                  <button 
                    onClick={startCamera} 
                    className="btn btn-primary" 
                    style={{ fontSize: "12px", padding: "6px 12px" }}
                  >
                    Start Live Face Verification
                  </button>
                )}

                {cameraError && (
                  <div className="alert alert-error" style={{ fontSize: "12px", padding: "8px", margin: "10px 0" }}>
                    ⚠️ {cameraError}
                  </div>
                )}

                {cameraActive && (
                  <div style={{ marginTop: "15px" }}>
                    <div style={{ position: "relative", width: "100%", maxWidth: "320px", borderRadius: "8px", overflow: "hidden", background: "#000" }}>
                      <video 
                        ref={videoRef} 
                        autoPlay 
                        playsInline 
                        muted 
                        style={{ width: "100%", display: "block" }} 
                      />
                      {/* Guidance Overlay Frame */}
                      <div style={{
                        position: "absolute",
                        top: "10%",
                        left: "15%",
                        width: "70%",
                        height: "80%",
                        border: "2px dashed rgba(255, 255, 255, 0.6)",
                        borderRadius: "50%",
                        pointerEvents: "none"
                      }} />
                    </div>

                    <div style={{ marginTop: "12px" }}>
                      {livenessStep === 1 && (
                        <div>
                          <p style={{ fontSize: "13px", fontWeight: "500", margin: "0 0 8px 0" }}>
                            👤 Position your face inside the frame and look straight.
                          </p>
                          <button 
                            onClick={handleCaptureStraight} 
                            className="btn btn-primary" 
                            style={{ fontSize: "12px", padding: "6px 12px" }}
                          >
                            Capture Straight Face
                          </button>
                        </div>
                      )}

                      {livenessStep === 2 && (
                        <div>
                          <p style={{ fontSize: "13px", fontWeight: "600", color: "#d97706", margin: "0 0 8px 0" }}>
                            👉 Action: Now turn your head slightly to the {targetAction}.
                          </p>
                          <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "0 0 8px 0" }}>
                            Keep your face inside the frame.
                          </p>
                          <button 
                            onClick={handleCaptureAction} 
                            className="btn btn-primary" 
                            style={{ fontSize: "12px", padding: "6px 12px" }}
                          >
                            Capture Movement
                          </button>
                        </div>
                      )}

                      {livenessStep === 3 && (
                        <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                          ⏳ Analyzing liveness sequence...
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {livenessResult && (
                  <div style={{ 
                    marginTop: "15px", 
                    padding: "12px", 
                    borderRadius: "6px", 
                    background: livenessResult.liveness_status === "PASSED" ? "rgba(16, 185, 129, 0.1)" : "rgba(217, 119, 6, 0.1)",
                    border: `1px solid ${livenessResult.liveness_status === "PASSED" ? "#10b981" : "#d97706"}`
                  }}>
                    <h5 style={{ margin: "0 0 6px 0", fontSize: "13px", fontWeight: "600" }}>
                      {livenessResult.liveness_status === "PASSED" ? "✓ Liveness Passed" : "⚠ Liveness Attention Required"}
                    </h5>
                    <p style={{ margin: 0, fontSize: "12px", color: "var(--text-color)" }}>
                      {livenessResult.reason}
                    </p>
                    <ul style={{ margin: "8px 0 0 0", paddingLeft: "15px", fontSize: "11px", color: "var(--text-muted)" }}>
                      <li>Quality: {livenessResult.face_quality} (Score: {livenessResult.quality_score?.toFixed(1) || "N/A"})</li>
                      <li>Dimensions: {livenessResult.face_width}x{livenessResult.face_height}px</li>
                    </ul>
                    
                    {livenessResult.liveness_status !== "PASSED" && (
                      <button 
                        onClick={handleLivenessRetry} 
                        className="btn btn-secondary" 
                        style={{ fontSize: "11px", padding: "4px 8px", marginTop: "10px" }}
                      >
                        Retry Capture
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

        {/* Actions panel */}
        <div className="btn-container">
          <button 
            type="button" 
            onClick={() => navigate("/dashboard/tutor")} 
            className="btn btn-secondary"
            disabled={processing}
          >
            Go to Dashboard
          </button>
          
          <button 
            type="button" 
            onClick={handleStartVerification} 
            className="btn btn-primary"
            disabled={processing || !hasCertificate || overallState === "PROCESSING"}
          >
            {processing ? "Evaluating..." : "Start Validation Pipeline"}
          </button>
        </div>

        {!hasCertificate && (
          <p style={{ color: "var(--error-color)", fontSize: "12px", marginTop: "12px", textAlign: "center" }}>
            * You must upload a certificate in the Tutor Profile settings before initiating validation.
          </p>
        )}
      </div>
    </div>
  );
}
