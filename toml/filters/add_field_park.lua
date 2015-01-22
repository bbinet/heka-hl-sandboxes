require "string"

local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local to_discard = { }

function process_message()
    local fields = {
	park = false
    }
    while true do
	typ, key, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[key] = value
	end
    end
    local tracker = string.match(fields.name, "^.*tracker(..).*$")

    if tracker ~= nil then
	if string.find(fields.name, "^.*mode$") then
	    if tonumber(fields.value) == 2 then
		if to_discard[tracker] then
		    fields['park'] = true
		end
		to_discard[tracker] = true
	    elseif to_discard[tracker] then
		to_discard[tracker] = false
	    end
	elseif to_discard[tracker] then
	    fields['park'] = true
	end
    end

    inject_message({
	Type = type_output,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Fields = fields
    })
    return 0
end
