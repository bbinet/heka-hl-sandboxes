require "string"

local list = read_config('matchers')
local list_item = { }

function init_list()
    for value in string.gmatch(list, "[%S]+") do
	local sandbox = read_config(value .. '_type_output')
	local regex   = read_config(value .. '_regex')

        if sandbox and regex then
            list_item[#list_item + 1] = {
		sandbox = sandbox,
	        regex   = regex
	    }
	end
    end
end

function process_message()
    local uuid = read_message('Fields[uuid]')
    local hostname = read_message('Fields[hostname]')
    local name = read_message('Fields[name]')
    local next_sandbox = nil

    if #list_item == 0 and list ~= nil then init_list() end

    for index, value in ipairs(list_item) do
	if string.find(name, "^" .. value.regex .. "$") ~= nil then
	    next_sandbox = value.sandbox
	    break
	end
    end

    if not next_sandbox then return -1 end
    local data = {
	Type    = next_sandbox,
	Payload = read_message('Payload'),
	Fields  = {
	    uuid = uuid,
	    hostname = hostname,
	    name  = name,
	    value = read_message('Fields[value]')
	 }
    }
    inject_message(data)
    return 0
end
