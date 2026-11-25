import { AxiosError } from "axios";

/** First human-readable message from a DRF error response. */
export function extractError(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data) {
    return firstMessage(err.response.data) ?? "Something went wrong. Please try again.";
  }
  return "Something went wrong. Please try again.";
}

function firstMessage(data: unknown): string | null {
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.length ? firstMessage(data[0]) : null;
  if (data && typeof data === "object") {
    const values = Object.values(data as Record<string, unknown>);
    return values.length ? firstMessage(values[0]) : null;
  }
  return data == null ? null : String(data);
}
