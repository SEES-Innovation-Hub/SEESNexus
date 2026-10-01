// Every backend response is wrapped in this shape (Tech Doc §5), errors included.
export interface Envelope<T> {
  status: "success" | "error";
  message: string;
  data: T | null;
}
