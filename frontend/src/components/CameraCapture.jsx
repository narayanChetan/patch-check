import { useEffect, useRef, useState } from "react";

/**
 * Live camera capture using getUserMedia.
 *
 * Real browser constraint, not a bug: getUserMedia only works on HTTPS
 * or localhost. If this component reports a permission error inside an
 * embedded/sandboxed preview, that's the browser enforcing that rule —
 * open the deployed app in a normal browser tab to use the camera.
 */
export default function CameraCapture({ onCapture }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [status, setStatus] = useState("");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function start() {
    if (!window.isSecureContext) {
      setStatus(`Camera needs HTTPS or localhost. This page is on ${location.protocol} — deploy or run it over a secure origin to use the camera.`);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus("Camera access isn't supported in this browser.");
      return;
    }
    setStatus("Requesting camera access…");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
      setStatus("Camera live — hold the label steady and flat.");
      setReady(true);
    } catch (err) {
      const map = {
        NotAllowedError: "Camera permission was denied. Allow camera access in your browser settings and retry.",
        NotFoundError: "No camera was found on this device.",
        NotReadableError: "The camera is already in use by another app.",
      };
      setStatus(map[err.name] || "Could not access the camera. You can upload a photo instead.");
    }
  }

  function stop() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  function playShutterSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const beep = (freq, dur, gainVal, delay) =>
        setTimeout(() => {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = "square";
          osc.frequency.setValueAtTime(freq, ctx.currentTime);
          gain.gain.setValueAtTime(gainVal, ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
          osc.connect(gain).connect(ctx.destination);
          osc.start();
          osc.stop(ctx.currentTime + dur);
        }, delay);
      beep(1800, 0.02, 0.16, 0);
      beep(700, 0.09, 0.14, 45);
    } catch {
      // Web Audio unavailable — silently skip the sound, capture still works.
    }
  }

  function capture() {
    if (!ready || !videoRef.current) return;
    playShutterSound();
    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob);
      },
      "image/jpeg",
      0.92
    );
  }

  return (
    <div>
      <div className="camera-video-wrap">
        <video ref={videoRef} muted playsInline autoPlay />
        <div className="camera-guide" />
      </div>
      <div className="camera-status">{status}</div>
      <button className="btn btn-primary" onClick={capture} disabled={!ready} style={{ width: "100%" }}>
        Capture &amp; scan
      </button>
    </div>
  );
}
