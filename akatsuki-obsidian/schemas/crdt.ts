export const enum OpType {
  INSERT  = 0,
  DELETE  = 1,
  UPDATE  = 2,
  MERGE   = 3,
}

export interface CrdtOperation {
  opId: string;             // "<nodeId>:<seq>"
  opType: OpType;
  nodeId: string;           // Unique node ID
  seq: number;              // Monotonic sequence
  lamport: number;          // Lamport timestamp
  position?: number;        // For text operations
  length?: number;
  value?: string;
  path?: string[];          // For nested objects
  deps: string[];          // Dependencies (opIds)
}

export interface CrdtSnapshot {
  nodeId: string;
  lamport: number;
  operations: CrdtOperation[];
  timestamp: number;
}

export const enum SyncStrategy {
  FULL        = "full",
  INCREMENTAL = "incremental",
  LIVE        = "live",
}

export interface SyncState {
  nodeId: string;
  lamport: number;
  lastSync: number;
  pendingOps: number;
  strategy: SyncStrategy;
}
