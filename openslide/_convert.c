/*
 * openslide-python - Python bindings for the OpenSlide library
 *
 * Copyright (c) 2015 Carnegie Mellon University
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of version 2.1 of the GNU Lesser General Public License
 * as published by the Free Software Foundation.
 *
 * This library is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

#include <Python.h>

typedef unsigned char u8;

#ifdef WORDS_BIGENDIAN
#define CA 0
#define CR 1
#define CG 2
#define CB 3
#else
#define CB 0
#define CG 1
#define CR 2
#define CA 3
#endif

static void
argb2rgba(u8 *buf, Py_ssize_t len)
{
    Py_ssize_t cur;

    for (cur = 0; cur < len; cur += 4) {
        u8 a = buf[cur + CA];
        u8 r = buf[cur + CR];
        u8 g = buf[cur + CG];
        u8 b = buf[cur + CB];
        if (a != 0 && a != 255) {
            r = r * 255 / a;
            g = g * 255 / a;
            b = b * 255 / a;
        }
        buf[cur + 0] = r;
        buf[cur + 1] = g;
        buf[cur + 2] = b;
        buf[cur + 3] = a;
    }
}

// Takes one argument: a contiguous buffer object.  Modifies it in place.
static PyObject *
_convert_argb2rgba(PyObject *self, PyObject *args)
{
    PyObject *ret = NULL;
    Py_buffer view;

    if (!PyArg_ParseTuple(args, "s*", &view))
        return NULL;
    if (!PyBuffer_IsContiguous(&view, 'A')) {
        PyErr_SetString(PyExc_ValueError, "Argument is not contiguous");
        goto DONE;
    }
    if (view.readonly) {
        PyErr_SetString(PyExc_ValueError, "Argument is not writable");
        goto DONE;
    }
    if (view.len % 4) {
        PyErr_SetString(PyExc_ValueError, "Argument has invalid size");
        goto DONE;
    }

    Py_BEGIN_ALLOW_THREADS
    argb2rgba(view.buf, view.len);
    Py_END_ALLOW_THREADS

    Py_INCREF(Py_None);
    ret = Py_None;

DONE:
    PyBuffer_Release(&view);
    return ret;
}

static PyMethodDef ConvertMethods[] = {
    {"argb2rgba", _convert_argb2rgba, METH_VARARGS,
        "Convert aRGB to RGBA in place."},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef convertmodule = {
    PyModuleDef_HEAD_INIT,
    "_convert",
    NULL,
    0,
    ConvertMethods
};

PyMODINIT_FUNC
PyInit__convert(void)
{
    return PyModule_Create(&convertmodule);
}
#else
PyMODINIT_FUNC
init_convert(void)
{
    Py_InitModule("_convert", ConvertMethods);
}
#endif
