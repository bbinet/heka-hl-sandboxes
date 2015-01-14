require "string"

local list = read_config('matchers')
local list_item = { }

function init_list()
    for value in string.gmatch(list, "[%S]+") do
	local regex   = read_config(value .. '_regex')
	local type_output= read_config(value .. '_type_output')
	if type_output == nil or regex == nil then
	    return 1
	end

	list_item[#list_item + 1] = {
	    type_output = type_output,
	    regex   = regex
	}
    end
end
init_list()

function process_message()
    local name = read_message('Fields[name]')
    local type_output = nil

    for index, value in ipairs(list_item) do
	if string.find(name, "^" .. value.regex .. "$") ~= nil then
	    type_output = value.type_output
	    break
	end
    end

    local data = {
	Type    = type_output,
	Timestamp = read_message('Timestamp'),
	Payload = read_message('Payload'),
	Fields  = {
	    name  = name,
	    value = read_message('Fields[value]')
	 }
    }

    inject_message(data)
    return 0
end
