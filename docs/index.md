# FastAPI-motor-oil

**This project is deprecated and replaced by [motorhead](volfpeter.github.io/motorhead), adding Pydantic v2 support along with a couple of smaller improvements. Please create an issue if you need help with the migration.**

`FastAPI-motor-oil` is a collection of async utilities for working with MongoDB and conveniently creating performant APIs with async web frameworks such a [FastAPI](https://fastapi.tiangolo.com/).

Key features:

- Database **model** design with `Pydantic`.
- Relationship support and validation using async **validators and delete rules** with a declarative, decorator-based syntax.
- Declarative **index** specification.
- Typed **utilities** for convenient model and API creation.
- Ready to use, customizable **async service layer** with **transaction support** that integrates all the above to keep your API and business logic clean, flexible, and easy to understand.

By providing a convenient, declarative middle layer between MongoDB and your API, `FastAPI-motor-oil` is halfway between an object document mapper (based on `Pydantic`) and a database driver (by wrapping the official, async `motor` driver).

## Installation

The library is available on PyPI and can be installed with:

```console
$ pip install fastapi-motor-oil
```

## Dependencies

The project depends on `motor` (the official async MongoDB driver, which is built on top of `pymongo` and `bson`) and `pydantic`.

## Contributing

Contributions are welcome.

## License

The library is open-sourced under the conditions of the [MIT license](https://choosealicense.com/licenses/mit/).
