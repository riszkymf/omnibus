# omnibus

Tired of writing tests for your endpoint? Omnibus is your solution! Omnibus is a Rest testing tools that test your Rest application without writing codes.

## Features
- Write test data in YAML or Postman, no code is needed.
- Run your test using request or curl for remote testing, or flask if you need coverage report on your local Rest application.
- Supports extract, generate, validate and binding mechanism that lets you perform full test scenarios.
- Write your mock data on exclusive yaml files.

## Usage

```raw
omnibus <command> [options]
```

-----------------------
## INDEX

* [Command List](docs/commands.md) : 

    Currently Omnibus have two main features :
    * omnibus run, where it works as black box testing on your remote API
    * omnibus cov, where it works as a yaml parser for pytest.cov with validation
* [Features](docs/features.md) : 
    Details on test validation, extraction, variable binding in yaml and variable generator

* [Postman](docs/postman.md) :
    Details on using Postman JSON file on omnibus

* [Benchmark](docs/benchmark.md):
    Writing Benchmark test

* [Test File](docs/test_file.md):
    Creating your first test file

* [Examples](docs/example):
    Example Files

