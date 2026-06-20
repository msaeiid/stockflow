import { AxiosError } from "axios";

export function extractError(err: unknown): string {
  if (err instanceof AxiosError && err.response?.data) {
    const data = err.response.data;
    if (typeof data === "string") return data;
    const firstKey = Object.keys(data)[0];
    const value = data[firstKey];
    return Array.isArray(value) ? value[0] : String(value);
  }
  return "Something went wrong. Please try again.";
}
