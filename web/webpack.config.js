# http://owaislone.org/blog/webpack-plus-reactjs-and-django/

var path = require("path")

module.exports = {
  entry: './opensubmit/static/assets/js/index',
  output: {
      path: path.resolve('./opensubmit/static/assets/bundles/'),
      filename: "[name]-[hash].js",
  },
  resolve: {
    modulesDirectories: ['node_modules', 'bower_components'],
    extensions: ['', '.js', '.jsx']
  },
}
