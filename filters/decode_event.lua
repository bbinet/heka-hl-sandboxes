require "string"
require "cjson"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local payload = read_message('Payload')
    local severity, msg = string.match(payload, '^(%d+) "(.*)"$')
    if severity == nil then
	return -1, "severity can't be nil"
    end
    if msg == nil then
	return -1, "msg can't be nil"
    end
    local fields = cjson.decode('{"msg":"' .. msg .. '"}')

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Payload = payload,
	Severity = severity,
	Fields = fields
    })
    return 0
end
