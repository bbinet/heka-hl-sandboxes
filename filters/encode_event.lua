require "string"
require "cjson"

local version = 0
local type_output = read_config('type_output') or error('you must initialize "type_output" option')

function process_message()
    -- check that both Severity and Fields[msg] exist
    local severity = read_message("Severity")
    if severity == nil then
	return -1, "severity can't be nil"
    end

    local msg = read_message('Fields[msg]')
    if msg == nil then
	return -1, "msg can't be nil"
    end
    
    local fields = {
	encoder_type = "event",
	encoder_version = version
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
	Payload = severity .. ' ' .. cjson.encode(msg),
	Timestamp = read_message('Timestamp'),
	Severity = read_message('Severity'),
	Fields = fields
    })
    return 0
end
