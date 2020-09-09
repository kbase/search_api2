# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

# [0.5.0] - 2020-09-09
### Added
- Search across all indexes within a prefix rather than using the
  `default_search` alias so that we can search automatically created indexes

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
