# Google Cloud REST API

## Overview
- This project is a REST API implemented using Google App Engine and Google Cloud Services (Datastore, Authentication Services).
- The API enables CRUD operations and relationships with three entities: Users, Boats, Loads. 
- Entities are modeled and stored in Google Datastore with the following relationships: Users create and own boats, loads can be created and assigned/unassigned to boats.
- User authorization is implemented by using Google OAuth provider. Upon sign up or login, the User is directed to OAuth endpoint and requested to grant authorization to their profile information. 
  Once authorization is confirmed, Users are redirected to a page displaying their user ID and JSON Web Token (JWT). 
- All endpoints related to CRUD operation for the BOAT entity are protected, and the User must provide a valid JWT as part of the request.
- API was tested using Postman collections and enviroment. 
- For more details please read the attached documentation.

## Documentation
```sh
[Google Cloud REST API Documentation](https://github.com/AnnaBKC/Google-Cloud_REST-API/blob/main/GCP-RestAPI-Documentation.pdf)
``` 



