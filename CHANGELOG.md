# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- fix SCT-2930: not honoring withPublic and withPrivate
- fix SCT-2931: maximum reported search results was 10,000 - fixed to report actual search results with > 10K.
- fix SCT-2932: throws error if object has been deleted
- fix SCT-2933, SCT-2956: Searchapi2 legacy endpoint uses jsonrpc 2.0 not 1.1
- fix SCT-2937: searchapi2/legacy search_objects should be tolerant of inaccessible workspaces
- fix SCT-2947: unauthenticated search not working correctly (no ws or narr info)
- fix SCT-2969: not honoring object_types
- fix SCT-2970: not narrowing search with additional terms

### Changed
- implement SCT-2966: add a "build and test" workflow for GitHub Actions which builds an image, runs tests, and pushes the resulting image too GH Container Registry.

## [0.4.9] - 2020-09-11
### Changed
- Use the AND operator for legacy full-text search

## [0.4.8] - 2020-09-09
### Fixed
- Set pagination parameters for the `search_workspace` method

## [0.4.7] - 2020-09-03
### Fixed
- Include narrative info parameter setting bug

## [0.4.6] - 2020-08-31
### Fixed
- Fixed the highlight fields for legacy search

## [0.4.5] - 2020-08-25
### Fixed
- Prevent removal of trailing slash in configured user profile URL
- Fix format string in error
