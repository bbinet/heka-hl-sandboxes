require "string"
require "table"

local regex = table.concat({
	"^(%d+)",	-- Timestamp
	"([%w.]+)",	-- Type
	"(.+)",		-- Payload
	"([0-7]+)",	-- Severity
	"|(.*)$"		-- Fields
}, ' ')

function process_message()
	payload = read_message('Payload')
	local Timestamp, Type, Payload, Severity, Fields = string.match(payload, regex)
	local fields = {}
	for field in string.gmatch(Fields, "%S+") do
		local name, value = string.match(field, "^(%w+):(%w+)$")
		fields[name] = value
	end

	inject_message({
		Timestamp = Timestamp,
		Type = Type,
		Payload = Payload,
		Severity = Severity,
		Fields = fields
	})
	return 0
end
