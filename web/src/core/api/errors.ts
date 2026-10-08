export interface QuotaPayload {
  metric: string;
  limit: number;
  used: number;
  resets_at?: string | null;
}

export class AppError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AppError";
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class HttpError extends AppError {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly details?: unknown
  ) {
    const detailMsg =
      typeof details === "string"
        ? details
        : (details as { detail?: string })?.detail || statusText || `HTTP Error ${status}`;
    super(detailMsg);
    this.name = "HttpError";
  }
}

export class UnauthorizedError extends HttpError {
  constructor(details?: unknown) {
    super(401, "Unauthorized", details);
    this.name = "UnauthorizedError";
  }
}

export class ForbiddenError extends HttpError {
  constructor(details?: unknown) {
    super(403, "Forbidden", details);
    this.name = "ForbiddenError";
  }
}

export class NotFoundError extends HttpError {
  constructor(details?: unknown) {
    super(404, "Not Found", details);
    this.name = "NotFoundError";
  }
}

export class ConflictError extends HttpError {
  constructor(details?: unknown) {
    super(409, "Conflict", details);
    this.name = "ConflictError";
  }
}

export class QuotaExceededError extends HttpError {
  public readonly quota: QuotaPayload;

  constructor(payload: QuotaPayload) {
    super(
      402,
      "Payment Required",
      `Monthly quota exceeded for ${payload.metric}. Used: ${payload.used}/${payload.limit}.`
    );
    this.name = "QuotaExceededError";
    this.quota = payload;
  }
}

export class RateLimitError extends HttpError {
  constructor(details?: unknown) {
    super(429, "Too Many Requests", details || "Too many requests. Please slow down.");
    this.name = "RateLimitError";
  }
}

export function parseHttpError(status: number, data: unknown, statusText = ""): HttpError {
  switch (status) {
    case 401:
      return new UnauthorizedError(data);
    case 402: {
      const q = (data as { metric?: string; limit?: number; used?: number; resets_at?: string }) || {};
      return new QuotaExceededError({
        metric: q.metric || "unknown",
        limit: q.limit ?? 0,
        used: q.used ?? 0,
        resets_at: q.resets_at,
      });
    }
    case 403:
      return new ForbiddenError(data);
    case 404:
      return new NotFoundError(data);
    case 409:
      return new ConflictError(data);
    case 429:
      return new RateLimitError(data);
    default:
      return new HttpError(status, statusText, data);
  }
}
