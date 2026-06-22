use serde::Serialize;
use serde_json::Value;

use crate::errors::VerifierError;

pub fn canonical_json<T: Serialize>(payload: &T) -> Result<String, VerifierError> {
    let value = serde_json::to_value(payload)?;
    Ok(canonical_value(&value))
}

fn canonical_value(value: &Value) -> String {
    match value {
        Value::Null => "null".to_string(),
        Value::Bool(value) => value.to_string(),
        Value::Number(value) => value.to_string(),
        Value::String(value) => {
            serde_json::to_string(value).expect("serializing a string cannot fail")
        }
        Value::Array(values) => {
            let items = values.iter().map(canonical_value).collect::<Vec<_>>();
            format!("[{}]", items.join(","))
        }
        Value::Object(map) => {
            let mut keys = map.keys().collect::<Vec<_>>();
            keys.sort();
            let fields = keys
                .into_iter()
                .map(|key| {
                    let name =
                        serde_json::to_string(key).expect("serializing an object key cannot fail");
                    let value = canonical_value(&map[key]);
                    format!("{name}:{value}")
                })
                .collect::<Vec<_>>();
            format!("{{{}}}", fields.join(","))
        }
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;

    use super::canonical_value;

    #[test]
    fn sorts_object_keys_and_removes_insignificant_whitespace() {
        let value = json!({"b": true, "a": [2, {"d": "x", "c": null}]});
        assert_eq!(
            canonical_value(&value),
            r#"{"a":[2,{"c":null,"d":"x"}],"b":true}"#
        );
    }
}
