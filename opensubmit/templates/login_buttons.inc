{% load projecttags %}

<section>
    <div class="row">
            <div class="col-md-2">
                Authentication with:
            </div>
            <div class="col-md-2">
                <a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.path }}" class="btn-auth btn-google"><b>Google</b></a>
            </div>
            <div class="col-md-2">
                <a href="{% url 'social:begin' 'twitter' %}?next={{ next }}" class="btn-auth btn-twitter"><b>Twitter</b></a>
            </div>
            <div class="col-md-2">
                <a href="{% url 'social:begin' 'github' %}?next={{ next }}" class="btn-auth btn-github"><b>GitHub</b></a>
            </div>
            <div class="col-md-3">
                <a href="{% url 'social:begin' 'openid' %}?next={{ next }}" class="btn-auth btn-openid"><b>{% setting 'LOGIN_DESCRIPTION' %}</b></a>
            </div>
    </div>
</section>
