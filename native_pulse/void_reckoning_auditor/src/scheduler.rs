use std::time::{Instant, Duration};

pub struct AuditScheduler {
    last_audit_time: Instant,
    last_audit_turn: u64,
    interval_time: Duration,
    interval_turn: u64,
}

impl AuditScheduler {
    pub fn new(interval_ms: u64, interval_turns: u64) -> Self {
        Self {
            last_audit_time: Instant::now(),
            last_audit_turn: 0,
            interval_time: Duration::from_millis(interval_ms),
            interval_turn: interval_turns,
        }
    }
    
    pub fn should_audit(&self, current_turn: u64) -> bool {
        let time_elapsed = self.last_audit_time.elapsed() >= self.interval_time;
        let turn_elapsed = current_turn - self.last_audit_turn >= self.interval_turn;
        
        time_elapsed || turn_elapsed
    }
    
    pub fn mark_audited(&mut self, current_turn: u64) {
        self.last_audit_time = Instant::now();
        self.last_audit_turn = current_turn;
    }
}
