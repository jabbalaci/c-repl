#include "prog1.h"

//////////////////////////////////////////////////////////////////////////////
//
//   Implementation
//

#include <stdio.h>
#include <string.h>

#define BUFSIZE 1024

/**
 * It returns a dynamically allocated string that
 * must be freed on the caller's side.
 */
string get_string(const char* prompt)
{
    char buf[BUFSIZE];

    printf("%s", prompt);
    fgets(buf, sizeof(buf), stdin);
    buf[strlen(buf) - 1] = '\0';

    return strdup(buf);
}
