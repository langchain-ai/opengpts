# Auth

By default, we're using cookies as a mock auth method. It's for trying out OpenGPTs.
For production, we recommend using JWT auth, outlined below.

## JWT Auth: Options

There are two ways to use JWT: Local and OIDC. The main difference is in how the key
used to decode the JWT is obtained. For the Local method, you'll provide the decode
key as a Base64-encoded string in an environment variable. For the OIDC method, the
key is obtained from the OIDC provider automatically.

### JWT OIDC

If you're looking to integrate with an identity provider, OIDC is the way to go.
It will figure out the decode key for you, so you don't have to worry about it.
Just set `AUTH_TYPE=jwt_oidc` along with the issuer and audience. Audience can
be one or many - just separate them with commas.

```bash
export AUTH_TYPE=jwt_oidc
export JWT_ISS=<issuer>
export JWT_AUD=<audience>  # or <audience1>,<audience2>,...
```

### JWT Local

To use JWT Local, set `AUTH_TYPE=jwt_local`. Then, set the issuer, audience,
algorithm used to sign the JWT, and the decode key in Base64 format.

```bash
export AUTH_TYPE=jwt_local
export JWT_ISS=<issuer>
export JWT_AUD=<audience>
export JWT_ALG=<algorithm>  # e.g. ES256
export JWT_DECODE_KEY_B64=<base64_decode_key>
```

Base64 is used for the decode key because handling multiline strings in environment
variables is error-prone. Base64 makes it a one-liner, easy to paste in and use.


## Making Requests

To make authenticated requests, include the JWT in the `Authorization` header as a Bearer token:

```
Authorization: Bearer <JWT>
```


