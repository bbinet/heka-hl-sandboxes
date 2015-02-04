require "cjson"
function process_message()
	inject_message(cjson.decode(read_message('Payload')))

	return 0
end
