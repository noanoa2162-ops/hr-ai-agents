type AnalysisPayload = {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  audio_file?: File;
  access_key?: string;
};

export const sendAnalysisData = async (payload: AnalysisPayload) => {
  let response: Response;
  const accessHeaders = payload.access_key
    ? { "X-Analysis-Key": payload.access_key }
    : undefined;

  if (payload.audio_file) {
    const formData = new FormData();
    formData.append("first_name", payload.first_name);
    formData.append("last_name", payload.last_name);
    formData.append("email", payload.email);
    formData.append("phone", payload.phone || "");
    formData.append("audio_file", payload.audio_file);
    response = await fetch("/analyze_complete", {
      method: "POST",
      headers: accessHeaders,
      body: formData,
    });
  } else {
    response = await fetch("/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...accessHeaders,
      },
      body: JSON.stringify({
        first_name: payload.first_name,
        last_name: payload.last_name,
        email: payload.email,
        phone: payload.phone,
      }),
    });
  }

  if (!response.ok) throw new Error(`שגיאה בשרת: ${response.status}`);
  return response.json();
};
