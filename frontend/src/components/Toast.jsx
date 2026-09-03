import { useCallback, useState } from "react";

export function useToast() {
  const [message, setMessage] = useState("");
  const [show, setShow] = useState(false);

  const toast = useCallback((msg) => {
    setMessage(msg);
    setShow(true);
    setTimeout(() => setShow(false), 2600);
  }, []);

  const ToastEl = <div className={`toast ${show ? "show" : ""}`}>{message}</div>;
  return { toast, ToastEl };
}
