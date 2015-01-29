require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    local payload = read_message('Payload')
    local fields = {
	msg = string.match(string.gsub(payload, '\\"', '"'), '^"(.*)"$')
    }

    if fields.msg == nil then --TODO: print error message
	return 0
    end

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
	Fields = fields
    })
    return 0
end