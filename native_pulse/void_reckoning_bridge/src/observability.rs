use pyo3::prelude::*;
use void_reckoning_shared::{CorrelationContext, Event, EventLog, EventSeverity};

#[pymodule]
pub fn observability(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CorrelationContext>()?;
    m.add_class::<Event>()?;
    m.add_class::<EventLog>()?;
    m.add_class::<EventSeverity>()?;
    Ok(())
}
