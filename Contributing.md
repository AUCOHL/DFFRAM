# Contributing
Contributions are welcome and encouraged!

The process: Please fork the repository and submit a pull request. Ensure that the pull request passes the CI script.

Ensure that your fork is **rebased**. This is important. Pull requests with merge conflicts will very likely be rejected on principle.

## How to rebase
Ensure that your local git clone's `origin` remote is *your own fork*:
```sh
git remote set-url origin https://github.com/<you>/DFFRAM
```

Ensure that your local git clone also has an `upstream` remote. You can add it via the command:
```sh
git remote get-url upstream
> fatal: No such remote 'upstream'
git remote add upstream https://github.com/Cloud-V/DFFRAM`
```

You can start a rebase by typing:
```sh
git fetch upstream
git rebase upstream/main
```

If there are no conflicts, you will not get any error messages. However, in the event you do: `git diff --name-only --diff-filter=U` will list the conflicts. Resolve all of your conflicts properly, then invoke the following:
```sh
git add .
git rebase --continue
```

Repeat the previous step until you get no error messages. Then finally, you need to rewrite your fork's history as follows:

```sh
git push -fu origin main
```

Then, create your pull request. If all went well, the CI should pass.

## Note to maintainers
If the number of commits is low, rebase and merge, but if it is high (5 commits or more), squash and merge.

Squash and merge makes for a cleaner commit history, but will require pretty much everyone to rebase any work they've had off the main branch with a great degree more difficulty.

# Legal
By submitting a pull request, you (the Contributor) hereby grant The American University in Cairo and the Cloud V Project a world-wide, royalty-free, non-exclusive license under intellectual property rights (other than patent or trademark) licensable by such Contributor to:

* use, reproduce, make available, modify, display, perform, distribute, and otherwise exploit its Contributions, either on an unmodified basis, with Modifications, or as part of a Larger Work;

* under Patent Claims of such Contributor to make, use, sell, offer for sale, have made, import, and otherwise transfer either its Contributions or its Contributor Version.

Copyright notice: above text adapted from the Mozilla Public License, version 2.0.

You are entitled and encouraged to add your name and email to the AUTHORS document at the root of the repository under 'Other Contributors', as well as include your name in any modified or created file.