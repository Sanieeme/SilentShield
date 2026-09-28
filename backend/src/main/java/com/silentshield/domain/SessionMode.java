package com.silentshield.domain;

/** Server-side only. Never exposed to the client (not in JWT, not in any response). */
public enum SessionMode { NORMAL, DURESS }
