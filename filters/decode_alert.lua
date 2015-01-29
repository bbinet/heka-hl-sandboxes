require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local payload = read_message('Payload')
    local severity, message = string.match(string.gsub(payload, '\\"', '"'), '^(%d+) "(.*)"$')
    if severity == nil or message == nil then --TODO: print error message
	return 0
    end

    local fields = {
	msg = message
    }

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
