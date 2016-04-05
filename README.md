### What is this?

It's a DIY asynchronous microframework project to further explore Python35+, software architecture and a few other interesting things.

Here are some of the things it demonstrates:

- [Dependency injection][1] and how it affects application design and ease of testing.
- How to use the comfortable `[asyncio.start_server][2]` interface to write asynchronous networking code.
- A naive approach to parsing HTTP requests and routing requests.
- A first try at [the Clean Architecture][3] based on Brandon Rhode's [The Clean Architecture in Python][4]. The business logic (parsing requests, routing requests, etc.) doesn't know a thing about IO, meaning, the IO depends on the entity and this dependency happens only one way.

Here's the inspiration behind this project:

- [http://justanr.github.io/exploring-code-architecture][5] (this made things really click together for me).
- [Ruby Midwest 2011 - Architecture: The Lost Years by Uncle Bob][6]
- [Ruby Conf 12 - Boundaries by Gary Bernhardt][7]
- [Refactoring Code that Accesses External Services][8]


### LICENSE

The MIT License (MIT)

Copyright (c) 2016 sirMackk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

[1]: https://en.wikipedia.org/wiki/Dependency_injection
[2]: https://docs.python.org/3/library/asyncio-stream.html
[3]: https://blog.8thlight.com/uncle-bob/2012/08/13/the-clean-architecture.html
[4]: https://www.youtube.com/watch?v=DJtef410XaM
[5]: http://justanr.github.io/exploring-code-architecture
[6]: https://www.youtube.com/watch?v=WpkDN78P884
[7]: https://www.youtube.com/watch?v=yTkzNHF6rMs
[8]: http://martinfowler.com/articles/refactoring-external-service.html
