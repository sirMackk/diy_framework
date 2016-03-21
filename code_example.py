### HELLO WORLD
#
# headers
# body
# get
# post
# route + params
# body params


# headers and body
async def home(r):
    rsp = Response()
    rsp.set_header('Content-Type', 'text/html')
    rsp.body = b'<html><body><b>test</b></body></html>'
    return rsp


# get route + params
async def welcome(r):
    return "Welcome {}".format(arg1)

# post route + body param
async def parse_form(r):
    if r.method == 'GET':
        return 'form'
    else:
        name = r.body_params.get('name', '')
        password = r.body_params.get('password', '')

        return "{0}:{1}".format(name, password)

## application = router + http server

router = Router()
router.add_routes({
    r'/': home,
    r'/welcome/{name}': welcome,
    r'/login': parse_form})

# add app to loop?
