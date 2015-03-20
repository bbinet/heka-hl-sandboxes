local version = 0
local type_output = read_config('type_output') or error('you must initialize "type_output" option')
local method = read_config('type_output_method') or 'overwrite'

if method ~= "prefix" and method ~= "suffix" and method ~= "overwrite" then
    return -1, "unknown type_output_method: supported methods are one of: "
               .. "[prefix|suffix|overwrite]"
end

function process_message()
    local fields = {
	encoder_type = "metric",
	encoder_version = version
    }

    while true do
	typ, name, value = read_next_field()
	if not typ then break end
	if typ ~= 1 then --exclude bytes
	    fields[name] = value
	end
    end

    if fields['name'] == nil then
	return -1, "Fields['name'] can't be nil"
    end
    if fields['value'] == nil then
	return -1, "Fields['value'] can't be nil"
    end

    local type_out = type_output
    if method == 'prefix' then
	type_out = type_output .. read_message('Type')
    elseif method == 'suffix' then
	type_out = read_message('Type') .. type_output
    end

    inject_message({
	Type = type_out,
	Payload = fields['name'] .. ' ' .. fields['value'],
	Timestamp = read_message('Timestamp'),
	Severity = read_message('Severity'),
	Fields = fields
    })
    return 0
end
