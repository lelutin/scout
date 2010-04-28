#!/usr/bin/env perl
#######################################################################
#    format-subst.pl translates tags from gitattributes
#    Copyright (C) 2010  Avery Pennarun <apenwarr@gmail.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Library General Public
#    License as published by the Free Software Foundation; either
#    version 2 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Library General Public License for more details.
#
#    You should have received a copy of the GNU Library General Public
#    License along with this library; if not, write to the Free
#    Software Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#######################################################################
use warnings;
use strict;

sub fix($) {
    my $s = shift;
    chomp $s;
    return $s;
}

while (<>) {
    s{
	\$Format:\%d\$
    }{
	fix(`git describe --match="v*" | sed 's/\\<v//'`);
    }ex;

    s{
	\$Format:([^\$].*)\$
    }{
	fix(`git log -1 --pretty=format:"$1"`)
    }ex;

    # Keep only the version tag from %d format of gitattributes
    s{
	\ *\(.*tag:\ v([^,]+).*\)\ *
    }{
	fix($1)
    }ex;
    print;
}
